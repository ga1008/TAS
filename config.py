# 文件位置: config.py
import os

base_dir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "supersecretkey123456")

    # AI 配置 (指向 AI 助手微服务)
    AI_ASSISTANT_BASE_URL = os.getenv("AI_ASSISTANT_ENDPOINT", "http://127.0.0.1:9011")
    AI_ASSISTANT_CHAT_ENDPOINT = f"{AI_ASSISTANT_BASE_URL.rstrip('/')}/api/ai/chat"

    # 数据库配置
    DB_PATH = os.path.join(base_dir, 'data', 'grading_system_v2.db')  # 建议改个名字，跟题库区分开

    GRADERS_DIR = os.path.join(base_dir, 'grading_core', 'graders')
    TRASH_DIR = os.path.join(base_dir, 'grading_core', 'trash')

    # 管理员配置
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    UPLOAD_FOLDER = os.path.join(base_dir, 'uploads')
    FILE_REPO_FOLDER = os.path.join(base_dir, 'uploads', 'file_repo')
    WORKSPACE_FOLDER = os.path.join(base_dir, 'workspaces')

    SIGNATURES_FOLDER = os.path.join(UPLOAD_FOLDER, 'signatures')

    TEMPLATE_DIR = os.path.join(base_dir, 'export_core', 'templates')

    # AI 欢迎语缓存配置
    AI_WELCOME_CACHE_TTL = 4 * 60 * 60  # 4小时缓存 (秒)


# === 基础 Prompt (保持不变的部分) ===
BASE_CREATOR_PROMPT = """
你是一名资深的 Python 自动化测试工程师和教育评估专家。请阅读以下【试卷内容】和【评分细则】，编写一个用于自动化批改系统的 Python 插件类。

### 1. 代码架构要求 (Strict)
- **输出**: 只输出一段完整的 Python 代码，包含在 ```python ... ``` 块中。
- **继承**: 必须导入 `from grading_core.base import BaseGrader, GradingResult` 并继承 `BaseGrader`。
- **类属性**: 
  - `ID`: 必须唯一。
  - `NAME`: 核心显示的名称，请务必将"{strictness_label}"标记包含在名称中，例如 "Java期末(宽松模式)"。
- **核心方法**: 实现 `def grade(self, student_dir, student_info) -> GradingResult:`。
- **结果对象**: 使用 `self.res.add_sub_score(name, score)` 记录分项，最后计算 `self.res.total_score`。
- 请仔细分析评分细则，将试卷划分为若干逻辑块（如 Task1, Task2, Task3...）。
- 每个逻辑块计算完分数后，调用 `self.res.add_sub_score(...)`。


### 2. 基类内置能力 (请直接调用，严禁重复实现)
父类 `BaseGrader` 已封装了以下底层逻辑，请务必直接调用。父类完整代码如下（部分符号由于逻辑原因改为文字描述）：
class GradingResult:
    def __init__(self):
        self.total_score = 0
        self.is_pass = False
        self.deduct_details = []
        self.sub_scores = []
    def add_sub_score(self, name, score, *args, **kwargs):
        try:
            score = float(score)
        except:
            score = 0
        self.sub_scores.append(左大括号"name": name, "score": score右大括号)
    def get_deduct_str(self, *args, **kwargs):
        return "; ".join(self.deduct_details) if self.deduct_details else ""
    def get_details_json(self, *args, **kwargs):
        return json.dumps(self.sub_scores, ensure_ascii=False)
    def add_deduction(self, msg, *args, **kwargs):
        self.deduct_details.append(msg)

class BaseGrader(abc.ABC):
    ID = "base"
    NAME = "Base Grader"
    
    def __init__(self):
        self.file_map = # 空字典
        
    @abc.abstractmethod
    def grade(self, student_dir, student_info, *args, **kwargs) -> GradingResult:
        pass

    def scan_files(self, root_dir, *args, **kwargs):
        self.file_map = # 空字典
        for root, _, files in os.walk(root_dir):
            for f in files:
                self.file_map[f.lower()] = os.path.join(root, f)
        return self.file_map

    def smart_find(self, target_filename, alternatives=None, ignore_subfixes=False, *args, **kwargs):
        if not self.file_map:
            raise RuntimeError("File map not initialized. Call self.scan_files(student_dir) first.")
        penalty = 0
        target_lower = target_filename.lower()
        if target_lower in self.file_map:
            real_path = self.file_map[target_lower]
            real_name = os.path.basename(real_path)
            if not ignore_subfixes and real_name != target_filename:
                penalty = 1
            return real_path, penalty
        if alternatives:
            for alt in alternatives:
                if alt.lower() in self.file_map:
                    return self.file_map[alt.lower()], 1  # 用了别名，通常扣1分规范分
        return None, 0

    def read_text_content(self, file_path, *args, **kwargs):
        if not file_path or not os.path.exists(file_path):
            return None
        encodings = ['utf-8', 'gbk', 'cp936', 'latin-1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except:
                continue
        return None

    def verify_command(self, content, result_obj: GradingResult, strict_regex, loose_regex, full_pts, name, *args, **kwargs):
        if not content:
            return 0
        # 1. 严格匹配
        if re.search(strict_regex, content, re.IGNORECASE | re.MULTILINE):
            return full_pts
        # 2. 宽容匹配 (如果不为空)
        if loose_regex and re.search(loose_regex, content, re.IGNORECASE | re.MULTILINE):
            half_pts = max(1, full_pts // 2)
            result_obj.add_deduction(name + " 命令/参数不完整或有误，得" + half_pts + "分")
            return half_pts
        # 3. 失败
        result_obj.add_deduction(name + " 未检测到有效关键命令-" + full_pts)
        return 0
        
"""


# === 风格控制 Prompt ===
STRICT_MODE_PROMPT = """
### 3. 评分风格要求：【严格模式 (Strict)】
- **文件名匹配**: 必须严格匹配文件名大小写（除非评分标准明确说不区分）。
- **命令检查**: 在使用 `verify_command` 时，主要依赖 `strict_regex`。如果学生命令参数有细微差别，应当判错或大幅扣分。
- **代码规范**: 对学生代码中的多余空格、不规范缩进进行扣分。
- **容错率**: 低。除显而易见的笔误外，不进行模糊猜测。
"""

LOOSE_MODE_PROMPT = """
### 3. 评分风格要求：【宽松模式 (Loose)】
- **文件名匹配**: 必须开启 `ignore_subfixes=True`，并尽可能提供 `alternatives` 列表（猜测学生可能使用的各种文件名变体）。
- **命令检查**: 在使用 `verify_command` 时，放宽 `strict_regex`，或者重点编写 `loose_regex`。只要关键命令词存在，即可给大部分分数。
- **容错率**: 高。尽量捞分，假设学生是初学者，只要逻辑大致对即可给分。忽略大小写错误、多余空格等问题。
"""


EXAMPLE_PROMPT = """

```python
### 输出示例
class ExamGrader(BaseGrader):
    ID = "linux_final_2026"     # 根据试卷和当前时间戳或者随机数编写一个独一无二的 ID
    NAME = "Linux 期末考试"       # 试卷名称加上一些修饰描述，使用中文

    def grade(self, student_dir, student_info) -> GradingResult:
        self.res = GradingResult()
        self.scan_files(student_dir) # 1. 扫描
        
        # --- 批改第一题 ---
        t1_score = 0
        path, pen = self.smart_find("1.png")
        if path: t1_score += 10
        # ... 其他逻辑 ...
        self.res.add_sub_score("Task 1: 截图", t1_score) # 记录分项
        
        # --- 批改第二题 ---
        t2_score = 0
        # ... 调用 verify_command ...
        self.res.add_sub_score("Task 2: 脚本编写", t2_score) # 记录分项
        
        # --- 后续题目（如果有）---
        ... ...

        # 汇总
        self.res.total_score = t1_score + t2_score + ...
        self.res.is_pass = self.res.total_score >= 60
        return self.res
```
"""

# === 核心提示词更新 ===
CREATOR_PROMPT = """
你是一名资深的 Python 自动化测试工程师和教育评估专家。请阅读以下【试卷内容】和【评分细则】，编写一个用于自动化批改系统的 Python 插件类。

### 1. 代码架构要求 (Strict)
- **输出**: 只输出一段完整的 Python 代码，包含在 ```python ... ``` 块中。
- **继承**: 必须导入 `from grading_core.base import BaseGrader, GradingResult` 并继承 `BaseGrader`。
- **核心方法**: 必须实现 `def grade(self, student_dir, student_info) -> GradingResult:`。
- **结果对象**: 
  - 初始化 `self.res = GradingResult()`。
  - **动态分项 (重要)**: 根据试题结构，多次调用 `self.res.add_sub_score(name, score)` 记录每个大题/模块的得分。例如：`self.res.add_sub_score("第一题:环境搭建", 20)`。
  - **总分计算**: 最终必须计算 `self.res.total_score` 并赋值。
  - **扣分详情**: 使用 `self.res.add_deduction(msg)` 记录扣分原因。使用中文简单描述。
  - 返回 `self.res`。
- **批改程序的打分要求**:
  - 必须严格按照【评分细则】进行评分，不能随意增减分项。
  - 必须确保评分细则中的每一条都被考虑到，并在代码中体现。
  - 一道题尽量适用多维度的匹配方式，避免简单的对错判断。
  - 尽可能考虑学生有可能写出的答案，例如英文大小写问题，多余空格问题，单词写错字母等，然后使用程序去校验并得出结论。
  - 一些无关紧要的地方，例如文件名等，尽量使用模糊匹配，避免学生因为小错误而被全盘否定。

### 2. 基类内置能力 (请直接调用，严禁重复实现)
父类 `BaseGrader` 已封装了以下底层逻辑，请务必直接调用。父类完整代码如下（部分符号由于逻辑原因改为文字描述）：
class GradingResult:
    def __init__(self):
        self.total_score = 0
        self.is_pass = False
        self.deduct_details = []
        self.sub_scores = []
    def add_sub_score(self, name, score, *args, **kwargs):
        try:
            score = float(score)
        except:
            score = 0
        self.sub_scores.append(左大括号"name": name, "score": score右大括号)
    def get_deduct_str(self, *args, **kwargs):
        return "; ".join(self.deduct_details) if self.deduct_details else ""
    def get_details_json(self, *args, **kwargs):
        return json.dumps(self.sub_scores, ensure_ascii=False)
    def add_deduction(self, msg, *args, **kwargs):
        self.deduct_details.append(msg)

class BaseGrader(abc.ABC):
    ID = "base"
    NAME = "Base Grader"
    
    def __init__(self):
        self.file_map = # 空字典
        
    @abc.abstractmethod
    def grade(self, student_dir, student_info, *args, **kwargs) -> GradingResult:
        pass

    def scan_files(self, root_dir, *args, **kwargs):
        self.file_map = # 空字典
        for root, _, files in os.walk(root_dir):
            for f in files:
                self.file_map[f.lower()] = os.path.join(root, f)
        return self.file_map

    def smart_find(self, target_filename, alternatives=None, ignore_subfixes=False, *args, **kwargs):
        if not self.file_map:
            raise RuntimeError("File map not initialized. Call self.scan_files(student_dir) first.")
        penalty = 0
        target_lower = target_filename.lower()
        if target_lower in self.file_map:
            real_path = self.file_map[target_lower]
            real_name = os.path.basename(real_path)
            if not ignore_subfixes and real_name != target_filename:
                penalty = 1
            return real_path, penalty
        if alternatives:
            for alt in alternatives:
                if alt.lower() in self.file_map:
                    return self.file_map[alt.lower()], 1  # 用了别名，通常扣1分规范分
        return None, 0

    def read_text_content(self, file_path, *args, **kwargs):
        if not file_path or not os.path.exists(file_path):
            return None
        encodings = ['utf-8', 'gbk', 'cp936', 'latin-1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except:
                continue
        return None

    def verify_command(self, content, result_obj: GradingResult, strict_regex, loose_regex, full_pts, name, *args, **kwargs):
        if not content:
            return 0
        # 1. 严格匹配
        if re.search(strict_regex, content, re.IGNORECASE | re.MULTILINE):
            return full_pts
        # 2. 宽容匹配 (如果不为空)
        if loose_regex and re.search(loose_regex, content, re.IGNORECASE | re.MULTILINE):
            half_pts = max(1, full_pts // 2)
            result_obj.add_deduction(name + " 命令/参数不完整或有误，得" + half_pts + "分")
            return half_pts
        # 3. 失败
        result_obj.add_deduction(name + " 未检测到有效关键命令-" + full_pts)
        return 0
        

### 3. 评分逻辑编写指南
- **结构化评分**: 
  - 请仔细分析评分细则，将试卷划分为若干逻辑块（如 Task1, Task2, Task3...）。
  - 每个逻辑块计算完分数后，调用 `self.res.add_sub_score(...)`。
- **容错性**: 只要 `smart_find` 找到了文件，就应当进行内容批改。

### 4. 输入素材
--- [试卷内容开始] ---
{exam_content}
--- [试卷内容结束] ---

--- [评分标准开始] ---
{grading_standard}
--- [评分标准结束] ---

### 5. 输出示例
```python
class ExamGrader(BaseGrader):
    ID = "linux_final_2026"     # 根据试卷和当前时间戳或者随机数编写一个独一无二的 ID
    NAME = "Linux 期末考试"       # 试卷名称加上一些修饰描述，使用中文

    def grade(self, student_dir, student_info) -> GradingResult:
        self.res = GradingResult()
        self.scan_files(student_dir) # 1. 扫描
        
        # --- 批改第一题 ---
        t1_score = 0
        path, pen = self.smart_find("1.png")
        if path: t1_score += 10
        # ... 其他逻辑 ...
        self.res.add_sub_score("Task 1: 截图", t1_score) # 记录分项
        
        # --- 批改第二题 ---
        t2_score = 0
        # ... 调用 verify_command ...
        self.res.add_sub_score("Task 2: 脚本编写", t2_score) # 记录分项
        
        # --- 后续题目（如果有）---
        ... ...

        # 汇总
        self.res.total_score = t1_score + t2_score + ...
        self.res.is_pass = self.res.total_score >= 60
        return self.res
```
"""