# grading_core/direct_grader_template.py


DIRECT_GRADER_TEMPLATE = """
import os
import json
import asyncio
import re
import base64
import mimetypes
from grading_core.base import BaseGrader, GradingResult
from database import Database
from ai_utils.volc_file_manager import VolcFileManager
from ai_utils.ai_helper import call_ai_platform_chat

db = Database()

class {class_name}(BaseGrader):
    ID = "{grader_id}"
    NAME = "{display_name}"
    COURSE = "{course_name}"

    # === 固化的核心知识库 (由 AI 预解析生成) ===
    EXAM_CONTENT = \"\"\"
{exam_content}
    \"\"\"

    GRADING_STANDARD = \"\"\"
{std_content}
    \"\"\"

    EXTRA_INSTRUCTION = \"\"\"
{extra_instruction}
    \"\"\"

    # 动态组装的系统 Prompt
    @property
    def system_prompt(self):
        # 注意：这里的 f-string 是生成的代码的一部分，所以用单花括号
        return f'''
你是一名极其严格且专业的阅卷专家。你的任务是根据提供的【试卷内容】和【评分细则】，对学生提交的作业（视频、图片或文档）进行评分。

【试卷内容】:
{{self.EXAM_CONTENT}}

【评分细则】:
{{self.GRADING_STANDARD}}

【额外指令】:
{{self.EXTRA_INSTRUCTION}}

【输出要求】:
1. 仔细对比学生的作业与评分细则。
2. 必须以合法的 JSON 格式输出，根对象包含:
   - "total_score" (数字): 总得分
   - "details" (数组): 每个得分项，包含 "name" (项目名) 和 "score" (得分)
   - "comment" (字符串): 简短的评语和扣分原因
3. 不要输出 Markdown 代码块标记（如 ```json），直接输出 JSON 字符串。
'''

    def grade(self, student_dir, student_info, *args, **kwargs) -> GradingResult:
        self.res = GradingResult()

        valid_files = []
        text_content_buffer = ""
        MAX_MEDIA_FILES = 10  # 硬限制：最多10个媒体文件
        media_count = 0
        SOFT_MEDIA_LIMIT = 5  # 软限制：5个文件时显示警告
        MAX_FILE_SIZE = 512 * 1024 * 1024  # 512 MB

        # 1. 扫描文件
        for root, _, files in os.walk(student_dir):
            for f in files:
                if f.startswith('.'): continue
                full_path = os.path.join(root, f)

                # 文件大小过滤
                try:
                    file_size = os.path.getsize(full_path)
                    if file_size > MAX_FILE_SIZE:
                        print(f"[Grader] 跳过超大文件: {{os.path.basename(full_path)}} ({{file_size / 1024 / 1024:.1f}} MB)")
                        self.res.add_deduction(f"跳过文件 {{os.path.basename(full_path)}} (超过512MB限制)")
                        continue
                except Exception as e:
                    print(f"[Grader] 无法获取文件大小 {{full_path}}: {{e}}")
                    continue

                ext = os.path.splitext(f)[1].lower()

                # 文本类作业
                if ext in ['.py', '.java', '.txt', '.md', '.c', '.cpp', '.html', '.css', '.js', '.doc', '.docx']:
                    try:
                        content = self.read_text_content(full_path)
                        if content:
                            # 注意：这里的双花括号是为了在 format 后保留单花括号
                            text_content_buffer += f"\\n--- 学生作业文件: {{f}} ---\\n{{content}}\\n"
                    except Exception as e:
                        print(f"[Grader] 读取文本文件失败 {{full_path}}: {{e}}")

                # 多媒体类作业
                elif ext in ['.jpg', '.png', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.heic', '.mp4', '.pdf', '.avi', '.mov']:
                    if media_count < MAX_MEDIA_FILES:
                        valid_files.append(full_path)
                        media_count += 1
                    elif media_count == SOFT_MEDIA_LIMIT:
                        # 软限制：显示警告但继续
                        print(f"[Grader] 媒体文件数量超过建议值 ({{SOFT_MEDIA_LIMIT}})，当前: {{media_count}}")
                        self.res.add_deduction(f"媒体文件过多({{media_count}}个)，建议控制在{{SOFT_MEDIA_LIMIT}}个以内")
                    else:
                        # 硬限制：拒绝处理
                        print(f"[Grader] 媒体文件数量超过硬限制 ({{MAX_MEDIA_FILES}})，当前: {{media_count}}")
                        self.res.add_deduction(f"媒体文件过多({{media_count}}个)，超过最大限制{{MAX_MEDIA_FILES}}")
                        return self.res

        # 2. 准备多媒体数据并构造消息内容
        try:
            ai_config = db.get_best_ai_config("vision")
            if not ai_config:
                 ai_config = db.get_best_ai_config("standard")

            if not ai_config:
                self.res.add_deduction("系统配置错误: 无可用 AI 模型")
                return self.res

            # 构造 content 列表 (Volcengine Responses API 格式)
            content_list = []

            # 添加文本内容
            if text_content_buffer:
                content_list.append({{
                    "type": "input_text",
                    "text": f"请根据上述标准对本条作业进行批改。\\n\\n【学生文本作业内容】:\\n{{text_content_buffer}}"
                }})

            # 处理多媒体文件
            if valid_files:
                # 只有视频和PDF需要上传器
                uploader = None
                if any(f.endswith(('.mp4', '.avi', '.mov', '.pdf')) for f in valid_files) and ai_config.get('api_key'):
                     uploader = VolcFileManager(api_key=ai_config['api_key'], base_url=ai_config.get('base_url'))

                for vf in valid_files:
                    vf_ext = os.path.splitext(vf)[1].lower()
                    is_video = vf_ext in ['.mp4', '.avi', '.mov']
                    is_pdf = vf_ext == '.pdf'
                    is_image = vf_ext in ['.jpg', '.png', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.heic']

                    try:
                        if is_video and uploader:
                            # 视频：上传到 Volcengine Files API
                            fid = uploader.upload_file(vf)
                            if fid:
                                content_list.append({{
                                    "type": "input_file",
                                    "file_id": fid
                                }})
                                print(f"[Grader] 视频文件已上传: {{os.path.basename(vf)}} -> {{fid}}")
                            else:
                                print(f"[Grader] 视频文件上传失败: {{os.path.basename(vf)}}")
                                self.res.add_deduction(f"视频文件处理失败: {{os.path.basename(vf)}}")
                        elif is_pdf and uploader:
                            # PDF：上传到 Volcengine Files API
                            fid = uploader.upload_file(vf)
                            if fid:
                                content_list.append({{
                                    "type": "input_file",
                                    "file_id": fid
                                }})
                                print(f"[Grader] PDF文件已上传: {{os.path.basename(vf)}} -> {{fid}}")
                            else:
                                print(f"[Grader] PDF文件上传失败: {{os.path.basename(vf)}}")
                                self.res.add_deduction(f"PDF文件处理失败: {{os.path.basename(vf)}}")
                        elif is_image:
                            # 图片：转换为 base64
                            mime_type, _ = mimetypes.guess_type(vf)
                            if not mime_type:
                                mime_type = 'image/png'

                            with open(vf, "rb") as image_file:
                                b64_str = base64.b64encode(image_file.read()).decode('utf-8')

                            content_list.append({{
                                "type": "input_image",
                                "image_url": {{
                                    "url": f"data:{{mime_type}};base64,{{b64_str}}"
                                }}
                            }})
                            print(f"[Grader] 图片已编码: {{os.path.basename(vf)}}")
                        else:
                            print(f"[Grader] 不支持的文件类型: {{vf}}")
                    except Exception as e:
                        print(f"[Grader] 处理文件失败 {{vf}}: {{e}}")
                        self.res.add_deduction(f"文件处理失败: {{os.path.basename(vf)}} - {{str(e)}}")
                        continue

            # 检查是否有有效内容
            if not content_list:
                self.res.add_deduction("未检测到有效的作业文件(支持图片/视频/代码/文档)")
                return self.res

            # 构造消息 (Volcengine Responses API 格式)
            messages = [
                {{
                    "role": "user",
                    "content": content_list
                }}
            ]

            # 3. 调用 AI
            response_json_str = asyncio.run(call_ai_platform_chat(
                system_prompt=self.system_prompt,
                messages=messages,
                platform_config=ai_config
            ))

            # 4. 解析结果
            # 正则表达式中的花括号也需要转义
            match = re.search(r'\{{.*\}}', response_json_str, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                self.res.total_score = float(data.get('total_score', 0))

                for d in data.get('details', []):
                    self.res.add_sub_score(str(d.get('name', '评分项')), float(d.get('score', 0)))

                if data.get('comment'):
                    self.res.add_deduction(str(data['comment']))
            else:
                self.res.total_score = 0
                self.res.add_deduction("AI 返回格式无法解析")
                print(f"[Grader] AI Raw Response: {{response_json_str}}")

        except Exception as e:
            self.res.total_score = 0
            self.res.add_deduction(f"批改服务异常: {{str(e)}}")
            import traceback
            traceback.print_exc()

        self.res.is_pass = self.res.total_score >= 60
        return self.res
"""
