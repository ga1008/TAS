
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

class DirectGrader_direct_85ef9ba0(BaseGrader):
    ID = "direct_85ef9ba0"
    NAME = "python程序设计进阶-网工2301班"
    COURSE = "None"

    # === 固化的核心知识库 (由 AI 预解析生成) ===
    EXAM_CONTENT = """
# 广西外国语学院课程考核试卷
## 2025 — 2026学年度第一学期
期末考试（√） 补考（ ） 重新学习考试（ ）

| 课程名称 | python程序设计进阶 |
| --- | --- |
| 学历层次 | 本科（√）/ 专科（ ） |
| 考核类型 | 考查(√) / 考试( ) |
| 专业年级班级 | 网工2301班 |
| 考试时间 | （90）分钟 |
| 试卷类型 | 开卷（√）/ 闭卷（ ） |
| 命题教师 | 张海林 |
| 系（教研室）主任 | 朱远坤 |
| 二级学院（部）主管教学领导 |  |

| 题号 | 一 | 二 | 总分 | 核分人 |
| --- | --- | --- | --- | --- |
| 满分 | 30 | 70 | 100 |  |
| 实得分 |  |  |  |  |

## 一、阅读以下说明，根据要求完成相关操作，并保存代码和截图（共 30 分）
### 1.
2025年全社会都在积极践行“碳达峰、碳中和”目标。某社区为了鼓励居民绿色出行，推出了一个绿色积分换礼品活动，根据平时出行使用的方式，计算获得的绿色积分以换取礼品。请你实现这个积分计算程序。

#### 操作步骤：
(1) 项目文件夹与文件创建(5 分)
a. 在桌面上创建一个以“班级-学号-姓名”命名的项目文件夹（例如：“网工2301-张三20230149666”）。
b. 在此文件夹内，新建一个Python文件，命名为 test1.py。

(2) 核心代码编写(20 分)
a. 打开 test1.py 文件，编写一个函数 calculate_green_points(transport_mode, distance)。
b. 函数能正确接收 transport_mode 和 distance 两个参数。
c. 函数能正确使用 if...elif...else 结构，按以下规则计算积分：

| 出行方式 | 每公里获得积分 |
| --- | --- |
| walk | 5 |
| bike | 3 |
| bus | 1 |
| car | 0 |
| 其他 | 0 |

d. 能正确处理 “其他” 未列出的出行方式（积 0 分），并确保函数返回(return)的积分为整数 (int)。

(3) 程序调用与结果截图(5 分)
a. 在函数定义下方的空白处，添加至少两行调用代码来测试你的函数，并打印结果。例如：
```python
print(f\"步行2.5公里，获得 {calculate_green_points('walk',2.5)} 积分\")
print(f\"开车10公里，获得 {calculate_green_points('cad',10.0)} 积分\")
```
b. 运行 test1.py 文件。
c. 将运行后显示打印结果的终端/控制台窗口截图。
d. 将截图命名为 test1-1.jpg，保存在你的“班级-学号-姓名”项目文件夹内。

## 二、根据以下操作说明，完成模拟登录应用，并保存代码和截图（共 70 分）
### 1.
近期针对我国 “国家授时中心”（NTSC）的网络安全威胁频发，一个安全、健壮的登录验证和日志记录流程至关重要。请你模拟实现一个带日志功能的系统登录程序。

#### 操作步骤：
(1) 文件夹与文件创建(5 分)
a. 在第一题创建的 “班级-学号-姓名” 项目文件夹内，新建一个Python文件，命名为 test2.py。

(2) 核心代码编写(45 分)
a. 打开test2.py，在文件中定义一个列表（如 USERS），用于保存初始化的三对账号和密码（其中最后一对密码是你的真实姓名+你自己创建一个任意密码）：

| username | passwd |
| --- | --- |
| 张三 | 123456 |
| 李四 | 654321 |
| 【你的姓名】 | 【你的自定义密码】 |

b. 程序运行时，首先请求用户输入 “账号”。程序必须比对账号是否存在。若不存在，则打印 “账号不存在” 并退出程序。
c. 如果账号正确，则进入密码比对。程序必须实现最多3次密码比对机会。
d. 密码错误时，提示 “密码错误，你还有 X 次机会。”；3次均错误后，提示 “登录失败” 并退出程序。
e. 密码正确时，提示 “登录成功！”。
f. 登录成功后，程序必须导入time模块获取当前时间，并以追加模式('a')将登录记录写入login.txt 文件中。
  - 日志格式要求：YYYY年mm月dd日 HH:MM:SS 姓名 （例如：2025年10月21日 23:30:15 张三）。
g. 写入 login.txt 文件的操作必须包含在 try...except 错误捕捉结构中。

(3) 成功登录截图(10 分)
a. 运行 test2.py 文件。
b. 使用你自己的姓名和自定义密码作为账号密码，模拟成功登录。
c. 将显示 “登录成功！” 的终端/控制台窗口截图。
d. 截图命名为 test2-1.jpg，保存在 “班级-学号-姓名” 项目文件夹内。

(4) 失败登录截图(5 分)
a. 再次运行 test2.py 文件。
b. 使用任意一个正确的账号（如 “李四”），但连续输入3次错误的密码。
c. 将显示3次错误提示及最终 “登录失败” 信息的终端/控制台窗口截图。
d. 截图命名为 test2-2.jpg，保存在 “班级-学号-姓名” 项目文件夹内。

(5) 文件提交(5 分)
将整个项目文件夹（例如 “网工2301-张三20230149666”）目录压缩成zip压缩包，命名为“姓名学号.zip”，例如“网工2301-张三20230149666.zip”，然后拖动到文件提交窗口。

（考试结束后，请与老师确认文件提交成功再关机！）

---
广西外国语学院课程考核试卷 第1页 共3页考试过程中不得将试卷拆开
广西外国语学院课程考核试卷 第2页 共3页考试过程中不得将试卷拆开
广西外国语学院课程考核试卷 第3页 共3页考试过程中不得将试卷拆开
    """

    GRADING_STANDARD = """
# 《Python程序设计进阶》课程非笔试考核评分细则

**课程信息**
- **课程名称**: Python程序设计进阶
- **专业年级班级**: 网工2301班
- **考核形式**: 机考
- **命题日期**: 2025年10月25日
- **命题教师**: 张海林
- **系（教研室）主任审核**: 朱远坤

## 一、 绿色积分计算器（共 30 分）

### 评分标准

1.  **正确创建项目文件夹与文件 (5 分)**

2.  **函数定义与参数 (共 5 分)**
    - a) (3 分) 能正确使用 `def` 关键字定义函数，函数名 `calculate_green_points` 基本正确（允许轻微拼写错误）。
    - b) (2 分) 函数能正确接收 `transport_mode` 和 `distance` 两个参数，参数名正确或接近，顺序不限。

3.  **核心逻辑判断与计算 (共 10 分)**
    *(本部分按四个主要分支给分，每个分支2.5分)*
    - a) (2.5 分) 能正确处理 `'walk'` (步行) 的情况：
        - 包含 `if` 或 `elif` 语句能正确判断字符串 `== 'walk'`。
        - 能正确执行公里数 * 5 的计算。
    - *(其他分支类似，如自行车、公共交通、私家车等，每个分支2.5分)*

4.  **兜底逻辑与返回 (共 5 分)**
    - a) (2 分) 包含 `else` 兜底分支：
        - 能正确使用 `else:` 语句来处理所有上述未列出的“其他”情况。
        - 在 `else` 分支中将积分正确设为 0。
    - b) (3 分) 函数的返回值：
        - (2 分) 函数在所有逻辑路径上最终都能使用 `return` 语句返回一个计算结果。
        - (1 分) 能确保返回的结果是 **整数 (int)** 类型（例如，使用了 `int()` 函数进行转换，或者计算结果本身即为整数）。
            - **扣分点说明**：如果学生 `return` 了正确的数值，但类型是 `float` (浮点数)，则此项的 (1 分) 不得分。

5.  **程序调用与结果截图 (5 分)**

## 二、 带日志功能的系统登录程序（共 70 分）

### 评分标准

1.  **正确创建文件夹与文件 (5 分)**

2.  **用户数据定义 (5 分)**
    - a) 能在代码中正确定义 `AUTHORIZED_USERS` 列表，数据结构为“列表嵌套字典”。
    - b) 必须正确包含了（学生本人的姓名、学号后4位）、“李四”和“张三”三组数据。

3.  **用户名验证逻辑 (10 分)**
    - a) (3 分) 能正确使用 `input()` 提示用户输入“账号”。
    - b) (4 分) 能正确遍历 `AUTHORIZED_USERS` 列表（例如使用 `for` 循环），并使用 `if` 判断查找匹配的用户名。
    - c) (3 分) 能正确处理“账号不存在”的情况：当循环结束仍未找到匹配时，打印“账号不存在”并退出程序。

4.  **密码验证与循环逻辑 (15 分)**
    - a) (5 分) 在用户名正确后，能使用 `while` 循环（或 `for` 循环）来控制“最多3次”尝试机会。
    - b) (5 分) 在循环内部，能正确提示输入“密码”，并比对密码是否正确。密码正确时，打印“登录成功”并跳出 (`break`) 循环。
    - c) (5 分) 密码错误时，能打印“密码错误，你还有 X 次机会。”；当 3 次均错误后，能打印“登录失败”并退出程序。

5.  **登录成功日志记录 (10 分)**
    - a) (3 分) 登录成功后，能正确导入 `datetime` 模块。
    - b) (3 分) 能正确获取当前时间，并使用 `.strftime()` 格式化为 `\"YYYY年mm月dd日 HH:MM:SS\"` 的样式。
    - c) (4 分) 能使用 `with open()` 以追加模式 (`'a'`) 和 `utf-8` 编码打开 `login.txt`，并按 `[时间] [用户名]\\n` 的格式正确写入日志。

6.  **关键错误捕捉 (5 分)**
    - a) (5 分) 在执行 (5.c) 中的文件写入操作时，代码块必须被 `try...except` 结构包裹，并且在 `except` 块中打印了指定的警告信息（如：“警告：日志写入失败！”）。

7.  **成功登录截图 (10 分)**
    - a) 截图内容清晰显示了使用学生本人姓名和学号后四位成功登录的终端界面。

8.  **失败登录截图 (5 分)**
    - a) 截图内容清晰显示了使用正确账号和连续3次错误密码，最终导致登录失败的终端界面。

9.  **最终项目打包 (5 分)**
    - a) 按要求将整个项目文件夹（包含第一、二题的所有文件和截图）正确压缩并命名为“网工2301-张三20230149666.zip”类似命名和格式。

---
**注**：只要最终达到登录验证结果，中间过程可酌情给分。
    """

    EXTRA_INSTRUCTION = """
尽可能给分。
需要注意匹配学生提交的文件有可能文件名命名不正确的问题，需要扩大匹配范围。例如test1.py有可能是test01.py、Text1.py、testl.py、test01.py.py等等，如果是py文件，则应该直接读取py文件并试图理解内容（根据题目特征、文件内容、长短等分辨是第几题的py文件），而不是纠结于文件名的问题。还有截图文件，除了命名问题有可能还存在后缀不匹配或者后缀大小写的问题，例如.png、.PNG、.jpg、.jpeg等等，尽可能匹配多种情况，避免漏掉学生的文件导致错误扣分（命名错误的情况扣一点点分即可），只要有截图，并且能分辨出来是包含了“1”、“2”等关键字的，就可以给截图分数。
代码方面，主要以内容为主，学生看起来理解了，那就可以给分。
总分100分，如果不满100分，需要请写清楚扣分项以及扣分的缘由。
    """

    # 动态组装的系统 Prompt
    @property
    def system_prompt(self):
        # 注意：这里的 f-string 是生成的代码的一部分，所以用单花括号
        return f'''
你是一名极其严格且专业的阅卷专家。你的任务是根据提供的【试卷内容】和【评分细则】，对学生提交的作业（视频、图片或文档）进行评分。

【试卷内容】:
{self.EXAM_CONTENT}

【评分细则】:
{self.GRADING_STANDARD}

【额外指令】:
{self.EXTRA_INSTRUCTION}

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
        MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB - 单张图片大小限制
        MAX_TEXT_LENGTH = 10000  # 文本内容最大字符数（防止 token 超限）

        # 1. 扫描文件
        for root, _, files in os.walk(student_dir):
            for f in files:
                if f.startswith('.'): continue
                full_path = os.path.join(root, f)

                # 获取文件扩展名（必须在文件大小检查之前）
                ext = os.path.splitext(f)[1].lower()

                # 文件大小过滤
                try:
                    file_size = os.path.getsize(full_path)
                    if file_size > MAX_FILE_SIZE:
                        print(f"[Grader] 跳过超大文件: {os.path.basename(full_path)} ({file_size / 1024 / 1024:.1f} MB)")
                        self.res.add_deduction(f"跳过文件 {os.path.basename(full_path)} (超过512MB限制)")
                        continue
                    # 额外检查：图片文件大小限制
                    if ext in ['.jpg', '.png', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.heic']:
                        if file_size > MAX_IMAGE_SIZE:
                            print(f"[Grader] 跳过大图片: {os.path.basename(full_path)} ({file_size / 1024 / 1024:.2f} MB)")
                            self.res.add_deduction(f"跳过图片 {os.path.basename(full_path)} (超过{MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB限制，请压缩后重试)")
                            continue
                except Exception as e:
                    print(f"[Grader] 无法获取文件大小 {full_path}: {e}")
                    continue

                # 文本类作业
                if ext in ['.py', '.java', '.txt', '.md', '.c', '.cpp', '.html', '.css', '.js', '.doc', '.docx']:
                    try:
                        content = self.read_text_content(full_path)
                        if content:
                            # 截断过长的文本内容（防止 token 超限）
                            if len(content) > 3000:  # 单个文件最多 3000 字符
                                content = content[:3000] + "\n[内容过长，已截断]"
                            # 检查总长度
                            if len(text_content_buffer) < MAX_TEXT_LENGTH:
                                # 注意：这里的双花括号是为了在 format 后保留单花括号
                                text_content_buffer += f"\n--- 学生作业文件: {f} ---\n{content}\n"
                            else:
                                print(f"[Grader] 文本内容过长，跳过文件: {f}")
                    except Exception as e:
                        print(f"[Grader] 读取文本文件失败 {full_path}: {e}")

                # 多媒体类作业
                elif ext in ['.jpg', '.png', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.heic', '.mp4', '.pdf', '.avi', '.mov']:
                    if media_count < MAX_MEDIA_FILES:
                        valid_files.append(full_path)
                        media_count += 1
                    elif media_count == SOFT_MEDIA_LIMIT:
                        # 软限制：显示警告但继续
                        print(f"[Grader] 媒体文件数量超过建议值 ({SOFT_MEDIA_LIMIT})，当前: {media_count}")
                        self.res.add_deduction(f"媒体文件过多({media_count}个)，建议控制在{SOFT_MEDIA_LIMIT}个以内")
                    else:
                        # 硬限制：拒绝处理
                        print(f"[Grader] 媒体文件数量超过硬限制 ({MAX_MEDIA_FILES})，当前: {media_count}")
                        self.res.add_deduction(f"媒体文件过多({media_count}个)，超过最大限制{MAX_MEDIA_FILES}")
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

            # 添加文本内容 (使用 type: "text" 而不是 "input_text")
            if text_content_buffer:
                # 截断过长的文本内容（防止 token 超限）
                if len(text_content_buffer) > MAX_TEXT_LENGTH:
                    text_content_buffer = text_content_buffer[:MAX_TEXT_LENGTH] + "\n[内容过长，已截断]"
                    print(f"[Grader] 文本内容过长，已截断到 {MAX_TEXT_LENGTH} 字符")
                content_list.append({
                    "type": "text",
                    "text": f"请根据上述标准对本条作业进行批改。\n\n【学生文本作业内容】:\n{text_content_buffer}"
                })

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
                                content_list.append({
                                    "type": "video_url",
                                    "video_url": {
                                        "url": fid
                                    }
                                })
                                print(f"[Grader] 视频文件已上传: {os.path.basename(vf)} -> {fid}")
                            else:
                                print(f"[Grader] 视频文件上传失败: {os.path.basename(vf)}")
                                self.res.add_deduction(f"视频文件处理失败: {os.path.basename(vf)}")
                        elif is_pdf and uploader:
                            # PDF：上传到 Volcengine Files API
                            fid = uploader.upload_file(vf)
                            if fid:
                                content_list.append({
                                    "type": "video_url",
                                    "video_url": {
                                        "url": fid
                                    }
                                })
                                print(f"[Grader] PDF文件已上传: {os.path.basename(vf)} -> {fid}")
                            else:
                                print(f"[Grader] PDF文件上传失败: {os.path.basename(vf)}")
                                self.res.add_deduction(f"PDF文件处理失败: {os.path.basename(vf)}")
                        elif is_image:
                            # 图片：转换为 base64 (使用 type: "image_url" 而不是 "input_image")
                            mime_type, _ = mimetypes.guess_type(vf)
                            if not mime_type:
                                mime_type = 'image/png'

                            with open(vf, "rb") as image_file:
                                b64_str = base64.b64encode(image_file.read()).decode('utf-8')

                            content_list.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_str}"
                                }
                            })
                            print(f"[Grader] 图片已编码: {os.path.basename(vf)}")
                        else:
                            print(f"[Grader] 不支持的文件类型: {vf}")
                    except Exception as e:
                        print(f"[Grader] 处理文件失败 {vf}: {e}")
                        self.res.add_deduction(f"文件处理失败: {os.path.basename(vf)} - {str(e)}")
                        continue

            # 检查是否有有效内容
            if not content_list:
                self.res.add_deduction("未检测到有效的作业文件(支持图片/视频/代码/文档)")
                return self.res

            # 构造消息 (Volcengine Responses API 格式)
            messages = [
                {
                    "role": "user",
                    "content": content_list
                }
            ]

            # 3. 调用 AI
            response_json_str = asyncio.run(call_ai_platform_chat(
                system_prompt=self.system_prompt,
                messages=messages,
                platform_config=ai_config
            ))

            # 4. 解析结果
            # 正则表达式中的花括号也需要转义
            match = re.search(r'\{.*\}', response_json_str, re.DOTALL)
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
                print(f"[Grader] AI Raw Response: {response_json_str}")

        except Exception as e:
            self.res.total_score = 0
            error_msg = str(e)
            # 检查是否是 token 超限错误
            if "Total tokens" in error_msg and "exceed max message tokens" in error_msg:
                friendly_msg = "作业内容过大（图片或文本过多），请减少图片数量或压缩图片大小后重试"
                self.res.add_deduction(friendly_msg)
                print(f"[Grader] Token 超限: {friendly_msg}")
            elif "Upstream API Error" in error_msg:
                # 提取上游 API 的实际错误信息
                import re
                api_error_match = re.search(r"'message':\s*'([^']+)'", error_msg)
                if api_error_match:
                    api_error = api_error_match.group(1)
                    self.res.add_deduction(f"AI 服务错误: {api_error}")
                    print(f"[Grader] API Error: {api_error}")
                else:
                    self.res.add_deduction(f"批改服务异常: {error_msg}")
            else:
                self.res.add_deduction(f"批改服务异常: {error_msg}")
            import traceback
            traceback.print_exc()

        self.res.is_pass = self.res.total_score >= 60
        return self.res
