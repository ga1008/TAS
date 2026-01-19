# services/ai_service.py
import asyncio
import json
import os
import re

import httpx
import pandas as pd

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
    def _parse_academic_year_semester(full_str):
        """
        从完整的学年学期字符串中解析出 academic_year 和 semester
        例如: "2025-2026学年度第一学期" -> ("2025-2026", "第一学期")
        """
        if not full_str:
            return None, None

        academic_year = None
        semester = None

        # 尝试匹配学年 (如 2025-2026)
        year_match = re.search(r'(\d{4})\s*[-－—–]\s*(\d{4})', full_str)
        if year_match:
            academic_year = f"{year_match.group(1)}-{year_match.group(2)}"

        # 尝试匹配学期 (如 第一学期, 第二学期, 第三学期)
        semester_match = re.search(r'(第[一二三]学期)', full_str)
        if semester_match:
            semester = semester_match.group(1)

        return academic_year, semester

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

            # 处理学年学期字段：如果只有 academic_year_semester，则拆分
            if meta.get('academic_year_semester') and (not meta.get('academic_year') or not meta.get('semester')):
                parsed_year, parsed_semester = AiService._parse_academic_year_semester(meta.get('academic_year_semester'))
                if parsed_year and not meta.get('academic_year'):
                    meta['academic_year'] = parsed_year
                if parsed_semester and not meta.get('semester'):
                    meta['semester'] = parsed_semester

            # 反过来：如果有 academic_year 和 semester 但没有 academic_year_semester，则合成
            if meta.get('academic_year') and meta.get('semester') and not meta.get('academic_year_semester'):
                meta['academic_year_semester'] = f"{meta.get('academic_year')}学年度{meta.get('semester')}"

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
    def generate_grader_worker(task_id, exam_text, std_text, strictness, extra_desc, max_score, app_config, course_name):
        """后台生成任务 (Thread Worker)"""

        # 注意：线程中无法直接获取 Flask 上下文，这里只做纯逻辑处理或传递必要参数
        # 实际 DB 操作在 database.py 中使用的是 check_same_thread=False，可以直接调用

        def update_status(status, log, grader_id=None):
            db.update_ai_task(task_id, status=status, log_info=log, grader_id=grader_id, course_name=course_name)

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

    @staticmethod
    def parse_student_list(file_id):
        """
        解析学生名单
        返回: (success, data, error_message)
        data 格式: {
            "metadata": {...},
            "students": [
                {"student_id": "...", "name": "...", "gender": "..."},
                ...
            ]
        }
        """
        record = db.get_file_by_id(file_id)
        if not record:
            return False, None, "文件记录不存在"

        # 如果已解析过，直接返回
        if record.get('parsed_content'):
            try:
                meta = json.loads(record.get('meta_info', '{}'))
            except:
                meta = {}
            # 需要重新解析学生列表
            return AiService._parse_student_list_from_content(
                record['parsed_content'], meta
            )

        physical_path = record['physical_path']
        ext = os.path.splitext(physical_path)[1].lower()

        # 1. 尝试 Vision 解析 (支持 docx, pdf, 图片)
        vision_config = db.get_best_ai_config("vision")
        if vision_config and ext in ['.docx', '.doc', '.pdf', '.jpg', '.png', '.xlsx', '.xls', '.csv']:
            try:
                target_path = physical_path

                # 转换非PDF文件
                if ext not in ['.pdf', '.jpg', '.png']:
                    from utils.file_converter import convert_to_pdf
                    converted = convert_to_pdf(physical_path)
                    if converted and os.path.exists(converted):
                        target_path = converted

                uploader = VolcFileManager(api_key=vision_config['api_key'],
                                          base_url=vision_config.get('base_url'))
                remote_id = uploader.upload_file(target_path)

                if remote_id:
                    from export_core.doc_config import DocumentTypeConfig
                    prompt = DocumentTypeConfig.get_prompt_by_type("student_list")

                    resp = asyncio.run(call_ai_platform_chat(
                        system_prompt="你是学生信息结构化专家。",
                        messages=[{"role": "user", "content": prompt, "file_ids": [remote_id]}],
                        platform_config=vision_config
                    ))

                    if resp and "[PARSE_ERROR]" not in resp:
                        # 保存解析结果
                        AiService._process_ai_json_response(resp, file_id, "student_list")

                        # 重新解析学生列表
                        updated_record = db.get_file_by_id(file_id)
                        meta = json.loads(updated_record.get('meta_info', '{}'))
                        return AiService._parse_student_list_from_content(
                            updated_record['parsed_content'], meta
                        )
            except Exception as e:
                pass  # 继续尝试其他方法

        # 2. 回退到 Text 模式
        success, raw_text = FileService.extract_text_from_file(physical_path)
        if success and raw_text:
            standard_config = db.get_best_ai_config("thinking") or db.get_best_ai_config("standard")
            if standard_config:
                from export_core.doc_config import DocumentTypeConfig
                prompt = DocumentTypeConfig.get_prompt_by_type("student_list")
                prompt += f"\n请解析以下内容并返回JSON：\n{raw_text[:50000]}"

                try:
                    resp = asyncio.run(call_ai_platform_chat(
                        system_prompt="你是学生信息结构化专家。",
                        messages=[{"role": "user", "content": prompt}],
                        platform_config=standard_config
                    ))

                    if resp:
                        AiService._process_ai_json_response(resp, file_id, "student_list")
                        updated_record = db.get_file_by_id(file_id)
                        meta = json.loads(updated_record.get('meta_info', '{}'))
                        return AiService._parse_student_list_from_content(
                            updated_record['parsed_content'], meta
                        )
                except Exception as e:
                    pass

        return False, None, "解析失败，请确保文件格式正确"

    @staticmethod
    def _parse_student_list_from_content(content, metadata):
        """
        从解析后的 Markdown 表格内容中提取学生列表
        """
        students = []
        has_gender = False

        lines = content.split('\n')
        data_started = False
        headers = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测表格分隔线
            if line.startswith('|---') or line.startswith('| ='):
                data_started = True
                continue

            if not line.startswith('|'):
                continue

            # 解析表格行
            parts = [p.strip() for p in line.split('|')[1:-1]]

            if not data_started:
                # 解析表头
                headers = [h.lower() for h in parts]
                if '性别' in headers or 'gender' in headers:
                    has_gender = True
                data_started = True
                continue

            # 解析数据行
            student = {}
            for i, header in enumerate(headers):
                if i < len(parts):
                    value = parts[i].strip()
                    if '学号' in header or 'student_id' in header:
                        student['student_id'] = value
                    elif '姓名' in header or 'name' in header:
                        student['name'] = value
                    elif '性别' in header or 'gender' in header:
                        student['gender'] = value

            # 只添加有学号和姓名的记录
            if student.get('student_id') and student.get('name'):
                students.append(student)

        return True, {
            "metadata": metadata,
            "students": students,
            "has_gender": has_gender,
            "student_count": len(students)
        }, None

    @staticmethod
    def parse_student_list_dedicated(file_id):
        """
        专门的学生名单解析函数：
        1. 对于 Excel/CSV 文件，使用 pandas 纯逻辑读取全部原始数据
        2. 直接从表格中提取学生列表（学号、姓名、性别等）
        3. AI 仅用于提取班级元数据（班级名称、学院、入学年份等）
        4. 减少格式转换可能带来的错误

        返回: (success, data, error_message)
        data 格式: {
            "metadata": {...},
            "students": [...],
            "has_gender": bool,
            "student_count": int
        }
        """
        record = db.get_file_by_id(file_id)
        if not record:
            return False, None, "文件记录不存在"

        # 如果已解析过，直接返回
        if record.get('parsed_content'):
            try:
                meta = json.loads(record.get('meta_info', '{}'))
            except:
                meta = {}
            return AiService._parse_student_list_from_content(
                record['parsed_content'], meta
            )

        physical_path = record['physical_path']
        ext = os.path.splitext(physical_path)[1].lower()

        # 1. 优先使用 pandas 直接读取 Excel/CSV 文件并提取学生数据
        if ext in ['.xlsx', '.xls', '.csv']:
            try:
                # 读取 Excel/CSV 文件
                if ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(physical_path, engine='openpyxl' if ext == '.xlsx' else 'xlrd')
                else:
                    # 尝试多种编码
                    encodings = ['utf-8', 'gb18030', 'gbk', 'latin1']
                    df = None
                    for enc in encodings:
                        try:
                            df = pd.read_csv(physical_path, encoding=enc)
                            break
                        except:
                            continue
                    if df is None:
                        raise Exception("无法读取CSV文件，编码可能不支持")

                # 清理列名（去除空格）
                df.columns = [str(c).strip() for c in df.columns]

                # 删除全空的行
                df = df.dropna(how='all')

                # 直接从DataFrame提取学生数据
                students, has_gender = AiService._extract_students_from_dataframe(df)

                if not students:
                    return False, None, "未能从文件中提取到学生数据，请检查文件格式是否包含学号和姓名列"

                # 使用 AI 提取班级元数据
                meta = AiService._extract_metadata_with_ai(df, file_id)

                # 保存解析结果
                markdown_table = AiService._students_to_markdown_table(students, meta)
                db.update_file_parsed_content(file_id, markdown_table)
                db.update_file_metadata(file_id, meta, doc_category="other")
                conn = db.get_connection()
                conn.execute("UPDATE file_assets SET meta_info=? WHERE id=?",
                           (json.dumps(meta, ensure_ascii=False), file_id))
                conn.commit()

                return True, {
                    "metadata": meta,
                    "students": students,
                    "has_gender": has_gender,
                    "student_count": len(students)
                }, None

            except Exception as e:
                import traceback
                traceback.print_exc()
                # 继续尝试其他方法

        # 2. 如果 pandas 读取失败或文件不是 Excel/CSV，使用常规文本提取
        success, raw_text_content = FileService.extract_text_from_file(physical_path)
        if success and raw_text_content:
            try:
                students, meta = AiService._extract_students_from_text(raw_text_content)
                if students:
                    # 保存解析结果
                    markdown_table = AiService._students_to_markdown_table(students, meta)
                    db.update_file_parsed_content(file_id, markdown_table)
                    db.update_file_metadata(file_id, meta, doc_category="other")
                    conn = db.get_connection()
                    conn.execute("UPDATE file_assets SET meta_info=? WHERE id=?",
                               (json.dumps(meta, ensure_ascii=False), file_id))
                    conn.commit()

                    return True, {
                        "metadata": meta,
                        "students": students,
                        "has_gender": any(s.get('gender') for s in students),
                        "student_count": len(students)
                    }, None
            except Exception as e:
                pass

        return False, None, "解析失败，请确保文件格式正确"

    @staticmethod
    def _dataframe_to_student_list_text(df):
        """
        将 DataFrame 转换为结构化文本，供 AI 分析
        保留原始数据格式，减少转换错误
        """
        lines = []

        # 添加表头
        headers = list(df.columns)
        lines.append(" | ".join(headers))
        lines.append("-" * len(" | ".join(headers)))

        # 添加数据行（限制前500行避免过长）
        for idx, row in df.head(500).iterrows():
            values = [str(v).strip() if pd.notna(v) else "" for v in row.values]
            lines.append(" | ".join(values))

        return "\n".join(lines)

    @staticmethod
    def _extract_students_from_text(text):
        """
        从文本中直接提取学生信息（不使用 AI）
        适用于格式规整的表格文本
        """
        import re
        students = []
        meta = {}

        lines = text.split('\n')

        # 查找表头
        header_idx = -1
        headers = []
        for i, line in enumerate(lines):
            if '学号' in line or '姓名' in line:
                headers = [h.strip().lower() for h in re.split(r'[|\t,，]+', line)]
                header_idx = i
                break

        if header_idx == -1:
            return [], meta

        # 查找列索引
        sid_idx = -1
        name_idx = -1
        gender_idx = -1

        for i, h in enumerate(headers):
            if '学号' in h or 'student' in h.lower() or 'id' in h.lower():
                sid_idx = i
            elif '姓名' in h or 'name' in h.lower():
                name_idx = i
            elif '性别' in h or 'gender' in h.lower():
                gender_idx = i

        if sid_idx == -1 or name_idx == -1:
            return [], meta

        # 提取学生数据
        for line in lines[header_idx + 1:]:
            if not line.strip():
                continue

            parts = re.split(r'[|\t,，]+', line)
            if len(parts) > max(sid_idx, name_idx):
                sid = parts[sid_idx].strip() if sid_idx < len(parts) else ""
                name = parts[name_idx].strip() if name_idx < len(parts) else ""

                if sid and name and not sid.replace('-', '').replace('_', '').isdigit():
                    # 过滤掉分隔行
                    continue

                if sid and name:
                    student = {"student_id": sid, "name": name}
                    if gender_idx >= 0 and gender_idx < len(parts):
                        student["gender"] = parts[gender_idx].strip()
                    students.append(student)

        return students, meta

    @staticmethod
    def _students_to_markdown_table(students, meta):
        """
        将学生列表转换为 Markdown 表格格式
        """
        lines = []

        # 添加元数据信息
        if meta.get('class_name'):
            lines.append(f"# {meta['class_name']} 学生名单\n")
            if meta.get('college'):
                lines.append(f"**学院**: {meta['college']}  ")
            if meta.get('enrollment_year'):
                lines.append(f"**入学年份**: {meta['enrollment_year']}  ")
            if meta.get('education_type'):
                lines.append(f"**培养类型**: {meta['education_type']}  ")
            lines.append("")

        # 构建表格
        has_gender = any(s.get('gender') for s in students)

        if has_gender:
            lines.append("| 学号 | 姓名 | 性别 |")
            lines.append("| --- | --- | --- |")
            for s in students:
                lines.append(f"| {s['student_id']} | {s['name']} | {s.get('gender', '')} |")
        else:
            lines.append("| 学号 | 姓名 |")
            lines.append("| --- | --- |")
            for s in students:
                lines.append(f"| {s['student_id']} | {s['name']} |")

        return "\n".join(lines)

    @staticmethod
    def _extract_students_from_dataframe(df):
        """
        直接从 DataFrame 提取学生数据（不使用 AI）
        自动识别学号、姓名、性别等列
        返回: (students_list, has_gender)
        """
        students = []

        # 打印调试信息
        print(f"[学生名单解析] Excel列名: {df.columns.tolist()}")
        print(f"[学生名单解析] 前5行数据:\n{df.head(5).to_string()}")

        # 查找列索引
        columns = df.columns.tolist()
        sid_idx = -1
        name_idx = -1
        gender_idx = -1
        email_idx = -1
        phone_idx = -1

        # 列名映射（支持多种命名方式）
        for i, col in enumerate(columns):
            col_clean = str(col).strip().lower()
            print(f"[学生名单解析] 列{i}: '{col}' -> 清理后: '{col_clean}'")

            # 学号列匹配 - 更精确的匹配
            if sid_idx == -1:
                # 精确匹配学号列（避免匹配到其他包含'id'的列）
                if col_clean == '学号' or col_clean == 'student_id' or col_clean == 'studentid':
                    sid_idx = i
                elif col_clean in ['student', 'id', '编号', '号']:
                    # 确保不匹配到姓名、性别等列
                    if not any(k in col_clean for k in ['姓名', 'name', '性别', 'gender']):
                        sid_idx = i

            # 姓名列匹配
            if name_idx == -1 and col_clean in ['姓名', 'name', '名字', 'student_name', 'studentname']:
                name_idx = i

            # 性别列匹配
            if gender_idx == -1 and col_clean in ['性别', 'gender', '男女性别']:
                gender_idx = i

            # 邮箱列匹配
            if email_idx == -1 and col_clean in ['邮箱', 'email', '邮件', 'mail']:
                email_idx = i

            # 电话列匹配
            if phone_idx == -1 and col_clean in ['电话', 'phone', '手机', '联系电话', '联系方式', 'tel']:
                phone_idx = i

        print(f"[学生名单解析] 识别结果: 学号列={sid_idx}, 姓名列={name_idx}, 性别列={gender_idx}")

        # 如果找不到学号和姓名列，尝试其他方式
        if sid_idx == -1 or name_idx == -1:
            print(f"[学生名单解析] 无法自动识别列名，尝试使用前两列")
            # 尝试使用前两列作为学号和姓名
            if len(columns) >= 2:
                sid_idx = 0
                name_idx = 1
            else:
                print(f"[学生名单解析] 列数不足，无法提取数据")
                return [], False

        # 提取学生数据
        for idx, row in df.iterrows():
            # 获取学号
            if pd.isna(row.iloc[sid_idx]) or str(row.iloc[sid_idx]).strip() == '':
                continue

            student_id = str(row.iloc[sid_idx]).strip()

            # 过滤掉表头行（如果学号列包含"学号"字样，说明是表头被当作数据了）
            if student_id in ['学号', 'student', 'id', '编号', 'student_id', 'studentid']:
                print(f"[学生名单解析] 跳过表头行 {idx}: 学号='{student_id}'")
                continue

            # 过滤掉分隔行（如"---"等）
            if student_id.replace('-', '').replace('_', '').replace('=', '').replace(' ', '').strip() == '':
                print(f"[学生名单解析] 跳过分隔行 {idx}: 学号='{student_id}'")
                continue

            # 获取姓名
            if name_idx >= 0 and not pd.isna(row.iloc[name_idx]):
                name = str(row.iloc[name_idx]).strip()
            else:
                name = ''

            # 过滤掉表头行（姓名列检查）
            if name in ['姓名', 'name', '名字', 'student_name', 'studentname']:
                print(f"[学生名单解析] 跳过表头行 {idx}: 姓名='{name}'")
                continue

            # 跳过姓名为空的记录
            if not name:
                continue

            student = {
                "student_id": student_id,
                "name": name
            }

            # 可选字段
            if gender_idx >= 0 and not pd.isna(row.iloc[gender_idx]):
                student["gender"] = str(row.iloc[gender_idx]).strip()
            if email_idx >= 0 and not pd.isna(row.iloc[email_idx]):
                student["email"] = str(row.iloc[email_idx]).strip()
            if phone_idx >= 0 and not pd.isna(row.iloc[phone_idx]):
                student["phone"] = str(row.iloc[phone_idx]).strip()

            students.append(student)

        print(f"[学生名单解析] 成功提取 {len(students)} 名学生")
        has_gender = gender_idx >= 0 and any(s.get('gender') for s in students)
        return students, has_gender

    @staticmethod
    def _extract_metadata_with_ai(df, file_id):
        """
        使用 AI 从 DataFrame 中提取班级元数据
        包括：班级名称、学院、系部、入学年份、培养类型等
        """
        meta = {
            "class_name": "",
            "college": "",
            "department": "",
            "enrollment_year": "",
            "education_type": "普本"
        }

        try:
            # 准备数据摘要给 AI 分析
            sample_data = df.head(10).to_string()
            columns_str = " | ".join(df.columns.tolist())

            prompt = f"""请分析以下学生名单表格，提取班级元数据。

表格列名: {columns_str}

前10行数据示例:
{sample_data}

请提取以下信息（如果表格中没有，请根据内容推测或留空）：
1. 班级名称 (class_name)
2. 学院 (college)
3. 系部 (department)
4. 入学年份 (enrollment_year)
5. 培养类型 (education_type，如：普本、专升本、专科等)

请以JSON格式返回，格式如下：
{{"class_name": "...", "college": "...", "department": "...", "enrollment_year": "...", "education_type": "..."}}"""

            standard_config = db.get_best_ai_config("thinking") or db.get_best_ai_config("standard")
            if standard_config:
                resp = asyncio.run(call_ai_platform_chat(
                    system_prompt="你是学生信息分析专家。请从表格数据中提取班级元信息，只返回纯JSON格式，不要有其他文字。",
                    messages=[{"role": "user", "content": prompt}],
                    platform_config=standard_config
                ))

                if resp:
                    # 清理并解析 JSON
                    cleaned = resp.strip()
                    # 尝试提取 JSON
                    import re
                    match = re.search(r'\{[^{}]*\}', cleaned)
                    if match:
                        cleaned = match.group(0)

                    try:
                        ai_meta = json.loads(cleaned)
                        # 合并 AI 提取的元数据
                        for key, value in ai_meta.items():
                            if value and str(value).strip():
                                meta[key] = str(value).strip()
                    except:
                        pass

        except Exception as e:
            import traceback
            traceback.print_exc()
            # AI 提取失败，使用默认值

        return meta

