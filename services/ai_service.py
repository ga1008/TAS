# services/ai_service.py
import asyncio
import json
import os
import re

import httpx

from ai_utils.ai_helper import call_ai_platform_chat
from ai_utils.volc_file_manager import VolcFileManager
from config import BASE_CREATOR_PROMPT, STRICT_MODE_PROMPT, LOOSE_MODE_PROMPT, EXAMPLE_PROMPT
from export_core.doc_config import DocumentTypeConfig
from extensions import db
from grading_core.factory import GraderFactory
from services.file_service import FileService
from utils.file_converter import convert_to_pdf


class AiService:
    @staticmethod
    def smart_parse_content(file_id, doc_category_hint="exam"):
        """
        智能解析统一入口：
        1. 优先尝试 Vision 模式 (V3)
        2. 失败则回退到 Text 模式 (V2)
        3. 均失败则回退到本地 Python 提取
        """
        record = db.get_file_by_id(file_id)
        if not record: return False, "文件记录不存在", {}

        # 缓存命中
        if record.get('parsed_content'):
            # 尝试恢复 meta_info
            try:
                meta = json.loads(record.get('meta_info', '{}'))
            except:
                meta = {}
            return True, record['parsed_content'], meta

        physical_path = record['physical_path']
        ext = os.path.splitext(physical_path)[1].lower()
        error_log = []

        # 1. 尝试 Vision 解析
        vision_config = db.get_best_ai_config("vision")
        if vision_config and ext in ['.docx', '.doc', '.pdf', '.jpg', '.png']:
            try:
                target_path = physical_path
                if ext != '.pdf' and ext not in ['.jpg', '.png']:
                    # 需要转换
                    converted = convert_to_pdf(physical_path)
                    if converted and os.path.exists(converted): target_path = converted

                uploader = VolcFileManager(api_key=vision_config['api_key'], base_url=vision_config.get('base_url'))
                remote_id = uploader.upload_file(target_path)

                if remote_id:
                    prompt = DocumentTypeConfig.get_prompt_by_type(doc_category_hint)
                    prompt += "\n【特别指令】请保持表格结构，识别勾选框，并以JSON格式返回 {content:..., metadata:...}。"

                    resp = asyncio.run(call_ai_platform_chat(
                        system_prompt="你是高校教学资料结构化专家。",
                        messages=[{"role": "user", "content": prompt, "file_ids": [remote_id]}],
                        platform_config=vision_config
                    ))
                    if resp and "[PARSE_ERROR]" not in resp:
                        return AiService._process_ai_json_response(resp, file_id, doc_category_hint)
            except Exception as e:
                error_log.append(f"Vision error: {e}")

        # 2. 回退到 Text 模式
        success, raw_text = FileService.extract_text_from_file(physical_path)
        if success and raw_text:
            standard_config = db.get_best_ai_config("thinking") or db.get_best_ai_config("standard")
            if standard_config:
                prompt = DocumentTypeConfig.get_prompt_by_type(doc_category_hint)
                prompt += f"\n请整理以下内容并返回JSON：\n{raw_text[:50000]}"
                try:
                    resp = asyncio.run(call_ai_platform_chat(
                        system_prompt="你是文档结构化专家。",
                        messages=[{"role": "user", "content": prompt}],
                        platform_config=standard_config
                    ))
                    return AiService._process_ai_json_response(resp, file_id, doc_category_hint)
                except Exception as e:
                    error_log.append(f"Text AI error: {e}")

        # 3. 彻底失败，保存纯文本
        if success and raw_text:
            db.update_file_parsed_content(file_id, raw_text)
            return True, raw_text, {}

        return False, f"所有解析策略均失败: {'; '.join(error_log)}", {}

    @staticmethod
    def _process_ai_json_response(json_text, file_id, doc_category):
        """内部辅助：清洗 JSON 并入库"""
        try:
            cleaned = json_text.strip()
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                # 简单的边界查找
                s, e = cleaned.find('{'), cleaned.rfind('}')
                if s != -1 and e != -1: cleaned = cleaned[s:e + 1]

            data = json.loads(cleaned)
            content = data.get("content", "")
            meta = data.get("metadata", {})

            if not content: content = json_text  # 兜底

            # 入库
            conn = db.get_connection()
            conn.execute('''UPDATE file_assets
                            SET parsed_content=?,
                                meta_info=?,
                                doc_category=?,
                                academic_year=?,
                                semester=?,
                                course_name=?,
                                cohort_tag=?
                            WHERE id = ?''',
                         (content, json.dumps(meta, ensure_ascii=False), doc_category,
                          meta.get('academic_year'), str(meta.get('semester', '')), meta.get('course_name'),
                          meta.get('cohort_tag'),
                          file_id))
            conn.commit()
            return True, content, meta
        except Exception as e:
            # 即使JSON解析失败，也保存原始内容
            db.update_file_parsed_content(file_id, json_text)
            return True, json_text, {}

    @staticmethod
    def generate_grader_worker(task_id, exam_text, std_text, strictness, extra_desc, max_score, app_config):
        """后台生成任务 (Thread Worker)"""

        # 注意：线程中无法直接获取 Flask 上下文，这里只做纯逻辑处理或传递必要参数
        # 实际 DB 操作在 database.py 中使用的是 check_same_thread=False，可以直接调用

        def update_status(status, log, grader_id=None):
            db.update_ai_task(task_id, status=status, log_info=log, grader_id=grader_id)

        try:
            update_status("processing", "正在组装 Prompt...")

            # 组装 Prompt (逻辑同原 app.py)
            prompt_parts = [BASE_CREATOR_PROMPT]
            strict_prompt = STRICT_MODE_PROMPT if strictness == 'strict' else (
                LOOSE_MODE_PROMPT if strictness == 'loose' else "### 3. 评分风格：标准模式")
            prompt_parts.append(strict_prompt)
            prompt_parts[0] = prompt_parts[0].replace("{strictness_label}", strictness)

            prompt_parts.append(f"### 4. 分数控制\n满分必须严格等于 **{max_score}分**。")
            if extra_desc: prompt_parts.append(f"### 5. 用户额外指令\n{extra_desc}")

            prompt_parts.append(f"### 6. 输入素材\n---试卷---\n{exam_text}\n---标准---\n{std_text}")
            prompt_parts.append(EXAMPLE_PROMPT)

            final_prompt = "\n".join(prompt_parts)

            # 调用 AI
            update_status("processing", "AI 正在生成代码...")
            payload = {
                "system_prompt": "你是一名资深的 Python 自动化测试工程师。",
                "messages": [], "new_message": final_prompt, "model_capability": "thinking"
            }

            # 这里的 Endpoint 需要从 config 传进来，或者硬编码，因为无法访问 app.config
            endpoint = app_config.get('AI_ASSISTANT_CHAT_ENDPOINT', "http://127.0.0.1:9011/api/ai/chat")

            response = httpx.post(endpoint, json=payload, timeout=600.0)
            if response.status_code != 200: raise Exception(f"AI Error: {response.text}")

            ai_content = response.json().get("response_text", "")

            # 提取代码
            code_match = re.search(r'```python(.*?)```', ai_content, re.DOTALL)
            code = code_match.group(1).strip() if code_match else ai_content

            # 提取 ID
            id_match = re.search(r'ID\s*=\s*["\']([^"\']+)["\']', code)
            if not id_match: raise Exception("未找到 ID 定义")
            grader_id = id_match.group(1)

            # 保存文件
            save_path = os.path.join(app_config['GRADERS_DIR'], f"{grader_id}.py")
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(code)

            # 热重载
            GraderFactory._loaded = False
            GraderFactory.load_graders()

            if grader_id in GraderFactory._graders:
                update_status("success", "生成成功", grader_id)
            else:
                update_status("failed", "代码生成但加载失败", grader_id)

        except Exception as e:
            update_status("failed", f"执行异常: {str(e)}")
