# grading_core/direct_grader_template.py

DIRECT_GRADER_TEMPLATE = """
import os
import json
import asyncio
import re
from grading_core.base import BaseGrader, GradingResult
from database import Database
from ai_utils.volc_file_manager import VolcFileManager
from ai_utils.ai_helper import call_ai_platform_chat

db = Database()

class {class_name}(BaseGrader):
    ID = "{grader_id}"
    NAME = "{display_name}"
    COURSE = "{course_name}"

    # === 固化的核心知识库 ===
    EXAM_CONTENT = \"\"\"
{exam_content}
    \"\"\"

    GRADING_STANDARD = \"\"\"
{std_content}
    \"\"\"

    EXTRA_INSTRUCTION = \"\"\"
{extra_instruction}
    \"\"\"

    # [NEW] 新增初始化方法，用于支持并发控制
    def __init__(self):
        super().__init__()
        # 1. 标记为 AI 核心
        self.is_ai_grader = True
        
        # 2. 提前获取 AI 配置
        # 这样做有两个好处：
        #   a) GradingService 可以通过 self.ai_provider_id 获取厂商 ID，从而限制并发数
        #   b) 避免批改每个学生时都重复查询数据库配置
        self.ai_config = db.get_best_ai_config("vision") or db.get_best_ai_config("standard")
        
        if self.ai_config:
            self.ai_provider_id = self.ai_config.get('provider_id')
        else:
            self.ai_provider_id = None

    @property
    def system_prompt(self):
        return f'''
你是一名极其严格且专业的阅卷专家。你的任务是根据【试卷内容】和【评分细则】，对学生提交的作业进行评分。

【试卷内容】:
{{self.EXAM_CONTENT}}

【评分细则】:
{{self.GRADING_STANDARD}}

【额外指令】:
{{self.EXTRA_INSTRUCTION}}

【输出要求】:
1. 必须以合法的 JSON 格式输出，根对象包含:
   - "total_score" (数字): 总得分
   - "details" (数组): 每个得分项，包含 "name" (项目名) 和 "score" (得分)
   - "comment" (字符串): 简短的评语和扣分原因
2. 不要输出 Markdown 代码块标记，直接输出 JSON 字符串。
'''

    def grade(self, student_dir, student_info, *args, **kwargs) -> GradingResult:
        self.res = GradingResult()

        valid_media_files = [] 
        text_content_buffer = ""

        MAX_MEDIA_FILES = 15
        media_count = 0
        MAX_FILE_SIZE = 512 * 1024 * 1024  # 512 MB
        MAX_TEXT_LENGTH = 15000  # 文本总长度限制

        # 1. 扫描文件
        for root, _, files in os.walk(student_dir):
            for f in files:
                if f.startswith('.'): continue
                full_path = os.path.join(root, f)
                ext = os.path.splitext(f)[1].lower()

                # 大小检查
                try:
                    file_size = os.path.getsize(full_path)
                    if file_size > MAX_FILE_SIZE:
                        self.res.add_deduction(f"跳过文件 {{f}} (超过512MB)")
                        continue
                except: continue

                # A. 文本类 (直接读取内容)
                if ext in ['.py', '.java', '.txt', '.md', '.c', '.cpp', '.html', '.css', '.js', '.json', '.sql']:
                    try:
                        content = self.read_text_content(full_path)
                        if content:
                            if len(content) > 5000:
                                content = content[:5000] + "\\n[...内容过长已截断]"

                            if len(text_content_buffer) < MAX_TEXT_LENGTH:
                                text_content_buffer += f"\\n=== 文件: {{f}} ===\\n{{content}}\\n"
                    except Exception as e:
                        print(f"[Grader] 读取文本失败: {{e}}")

                # B. 媒体类 (图片/视频/PDF)
                elif ext in ['.jpg', '.png', '.jpeg', '.gif', '.webp', '.bmp', '.mp4', '.avi', '.mov', '.pdf']:
                    if media_count < MAX_MEDIA_FILES:
                        valid_media_files.append(full_path)
                        media_count += 1
                    else:
                        self.res.add_deduction(f"媒体文件过多，跳过: {{f}}")

        # 2. 准备调用 AI
        try:
            ai_config = db.get_best_ai_config("vision") or db.get_best_ai_config("standard")
            if not ai_config:
                self.res.add_deduction("系统未配置 AI 模型")
                return self.res

            content_list = []

            # (1) 添加文本内容
            if text_content_buffer:
                content_list.append({{
                    "type": "input_text", 
                    "text": f"【学生代码/文本作业集合】:\\n{{text_content_buffer}}"
                }})

            # (2) 上传并添加媒体文件
            if valid_media_files and ai_config.get('api_key'):
                uploader = VolcFileManager(api_key=ai_config['api_key'], base_url=ai_config.get('base_url'))

                for vf in valid_media_files:
                    try:
                        ext = os.path.splitext(vf)[1].lower()
                        fid = uploader.upload_file(vf)

                        if fid:
                            # 关键修复：根据文件类型指定 input type
                            if ext in ['.jpg', '.png', '.jpeg', '.gif', '.webp', '.bmp']:
                                content_list.append({{
                                    "type": "input_image",
                                    "file_id": fid
                                }})
                            elif ext in ['.mp4', '.avi', '.mov']:
                                content_list.append({{
                                    "type": "input_video",
                                    "file_id": fid
                                }})
                            elif ext == '.pdf':
                                content_list.append({{
                                    "type": "input_file",
                                    "file_id": fid
                                }})

                            print(f"[Grader] 文件已上传: {{os.path.basename(vf)}} -> {{fid}} (Type: {{ext}})")
                        else:
                            self.res.add_deduction(f"文件上传失败: {{os.path.basename(vf)}}")
                    except Exception as e:
                        print(f"[Grader] 上传异常: {{e}}")

            if not content_list:
                self.res.add_deduction("未找到有效作业文件")
                return self.res

            # 3. 调用 AI
            response_json_str = asyncio.run(call_ai_platform_chat(
                system_prompt=self.system_prompt,
                messages=[{{"role": "user", "content": content_list}}],
                platform_config=ai_config
            ))

            # 4. 解析结果
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

        except Exception as e:
            self.res.total_score = 0
            self.res.add_deduction(f"批改服务异常: {{str(e)}}")
            import traceback
            traceback.print_exc()

        self.res.is_pass = self.res.total_score >= 60
        return self.res
"""