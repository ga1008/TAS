# services/ai_prompts.py
"""
AI 提示词模板和页面上下文定义
用于 AI 欢迎语生成系统
"""

from enum import Enum
from datetime import datetime


class PageContext(Enum):
    """页面上下文标识符，用于生成针对性的欢迎语"""

    DASHBOARD = "dashboard"
    TASKS = "tasks"
    STUDENT_LIST = "student_list"
    AI_GENERATOR = "ai_generator"
    EXPORT = "export"

    @classmethod
    def from_path(cls, path: str) -> 'PageContext':
        """根据请求路径确定页面上下文"""
        path_map = {
            '/': cls.DASHBOARD,
            '/tasks': cls.TASKS,
            '/student/': cls.STUDENT_LIST,
            '/students/': cls.STUDENT_LIST,
            '/ai_generator': cls.AI_GENERATOR,
            '/export': cls.EXPORT
        }
        for pattern, context in path_map.items():
            if path.startswith(pattern):
                return context
        return cls.DASHBOARD  # 默认


# ==================== AI 提示词模板 ====================

WELCOME_PROMPT_TEMPLATE = """你是一个智能教学助手的欢迎语生成器。你的任务是根据用户当前的上下文生成一句简短、专业且温暖的欢迎语或操作建议。

### 核心原则
1. **直接输出内容**：绝对不要包含"你好"、"欢迎语："、引号或任何前缀后缀。
2. **拒绝废话**：Standard模型容易啰嗦，请务必精简，直击重点。
3. **情绪价值**：语气要积极、肯定，让用户感到被支持。
4. **行动导向**：基于"最近操作"推测用户下一步意图。

### 用户画像
- 用户名: {username}
- 当前环境: {current_time} ({weekday} {time_period})
- 统计数据: 
  - 待处理任务: {pending_task_count}
  - 已有班级: {class_count}
  - 已上传文件: {file_count}
  - 评分核心: {grader_count}
- 最近操作(按时间倒序): 
{recent_actions_str}

### 页面上下文: {page_context_display}

### 生成逻辑示例 (Few-Shot)
1. **场景**: 用户刚上传了"期末试卷.docx" (最近操作)，在"工作台首页"。
   **输出**: 收到您的试卷文件，快去AI生成器创建对应的自动评分标准吧。

2. **场景**: 用户有 3 个待处理任务，现在是晚上 9 点。
   **输出**: 夜深了，您还有3个任务挂起，处理完早点休息，注意身体。

3. **场景**: 用户刚创建了新班级，但学生数为 0。
   **输出**: 新班级已建立，记得导入学生名单，以便后续管理成绩。

4. **场景**: 无特别操作，周一早晨。
   **输出**: 周一早安！新的一周，让我们高效开启教学工作。

请现在根据上述信息，生成一条欢迎语:
"""

# 页面特定的提示词扩展 (针对 Standard 模型简化并强化指令)
PAGE_SPECIFIC_PROMPTS = {
    PageContext.DASHBOARD: WELCOME_PROMPT_TEMPLATE,

    PageContext.TASKS: """你是一个任务列表页的引导助手。

### 用户状态
- 待处理: {pending_task_count}
- 批改中: {class_count}

### 任务
生成一句引导语。若有待处理任务，催促（温柔地）处理；若无，鼓励创建。
长度限制：30字以内。不要引号。

### 示例
- 还有 {pending_task_count} 个任务在队列中，喝杯咖啡等待AI处理完成吧。
- 目前没有积压任务，是个创建新批改计划的好时机。

请生成:
""",

    PageContext.STUDENT_LIST: """你是一个学生名单管理页的引导助手。

### 用户状态
- 学生总数: {student_count}
- 现有班级: {class_count}

### 任务
生成一句关于学生管理的建议。
长度限制：30字以内。不要引号。

### 示例
- 已管理 {student_count} 名学生，您可以随时导出他们的平时成绩。
- 只有准确的名单才能确保成绩录入无误，建议定期检查。

请生成:
""",

    # ... (Other contexts ai_generator, export follow similar pattern of strict constraints)
    PageContext.AI_GENERATOR: """你是一个AI生成器页的助手。

### 用户状态
- 已有核心: {grader_count}
- 最近上传文件数: {file_count}

### 任务
生成一句关于创建评分核心的建议。如果用户刚上传文件，提示利用该文件。
长度限制：35字以内。不要引号。

### 示例
- 利用刚上传的文件，只需几步即可生成专属评分脚本。
- 准确的评分标准是AI批改的关键，请详细描述您的要求。

请生成:
""",

    PageContext.EXPORT: """你是一个数据导出页的助手。

### 任务
生成一句关于成绩导出的建议。
长度限制：30字以内。不要引号。

### 示例
- 批改完成后，一键导出详细的成绩分析报表。
- 支持多种格式导出，方便您进行后续的教学存档。

请生成:
"""
}


# ==================== 时间段相关 ====================

def get_time_period() -> str:
    """获取当前时间段"""
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 23:
        return "evening"
    else:
        return "night"


def get_time_period_chinese() -> str:
    """获取当前时间段的中文描述"""
    hour = datetime.now().hour
    if 4 <= hour < 8:
        return "early_morning"
    elif 8 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "night"


def get_weekday_chinese() -> str:
    """获取中文星期"""
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    return weekdays[datetime.now().weekday()]


# ==================== 回退消息 ====================

FALLBACK_MESSAGES = {
    "early_morning": "清晨了，新的一天即将开始，准备好高效工作了吗？",
    "morning": "早安！新的一天开始了，准备好处理批改任务了吗？",
    "afternoon": "下午好！保持专注，今天还有许多任务等待完成。",
    "evening": "晚上好！今天辛苦了，继续加油，离目标不远了。",
    "night": "夜深了，注意休息。明天继续高效工作！"
}


def get_fallback_message(time_period: str = None) -> str:
    """
    获取基于时间的回退欢迎语

    Args:
        time_period: 时间段 (early_morning, morning, afternoon, evening, night)
                    如果为 None，则自动检测当前时间

    Returns:
        欢迎语文本
    """
    if time_period is None:
        time_period = get_time_period_chinese()

    # 映射时间周期
    period_map = {
        "early_morning": "early_morning",
        "morning": "morning",
        "afternoon": "afternoon",
        "evening": "evening",
        "night": "night"
    }

    mapped_period = period_map.get(time_period, "morning")
    return FALLBACK_MESSAGES.get(mapped_period, FALLBACK_MESSAGES["morning"])


def get_page_context_display(page_context: str) -> str:
    """获取页面上下文的中文显示名称"""
    display_map = {
        "dashboard": "工作台首页",
        "tasks": "批改任务列表",
        "student_list": "学生名单管理",
        "ai_generator": "AI 生成器",
        "export": "成绩导出",
        "library": "文档库"
    }
    return display_map.get(page_context, "工作台")


# ==================== AI 对话助手提示词 (Feature 002) ====================

def get_conversation_system_prompt(username: str, page_context: str = None) -> str:
    """
    获取对话系统提示词

    Args:
        username: 用户名
        page_context: 当前页面上下文

    Returns:
        系统提示词
    """
    page_display = get_page_context_display(page_context) if page_context else "系统"
    time_period = get_time_period_chinese()

    # 时间问候映射
    time_greeting = {
        "early_morning": "清晨好",
        "morning": "早上好",
        "afternoon": "下午好",
        "evening": "晚上好",
        "night": "夜深了"
    }.get(time_period, "你好")

    return f"""你是一个智能教学助手，正在与 {username} 老师对话。当前用户在「{page_display}」页面。

### 核心原则
1. **友好专业**：语气温暖但不啰嗦，像一个得力的助教。
2. **理解上下文**：用户当前在「{page_display}」页面，回答要与该页面功能相关。
3. **行动导向**：尽可能给出具体的操作建议，而非泛泛而谈。
4. **简洁有力**：回复控制在 100 字以内，除非用户明确要求详细解释。

### 系统功能概述
- **工作台首页**: 查看数据概览、待办任务
- **批改任务列表**: 管理 AI 批改任务的进度
- **AI 生成器**: 上传试卷和评分标准，生成批改核心
- **学生名单管理**: 导入、管理学生信息
- **成绩导出**: 导出批改结果为 Excel
- **文档库**: 管理试卷、资料文档

### 当前时间: {time_greeting}

请用简洁、专业、友好的语气回复用户的问题。"""


def get_page_greeting_prompt(username: str, page_context: str) -> str:
    """
    获取页面问候提示词

    Args:
        username: 用户名
        page_context: 页面上下文

    Returns:
        提示词
    """
    page_display = get_page_context_display(page_context)
    time_period = get_time_period_chinese()
    weekday = get_weekday_chinese()

    time_greeting = {
        "early_morning": "清晨好",
        "morning": "早上好",
        "afternoon": "下午好",
        "evening": "晚上好",
        "night": "夜深了"
    }.get(time_period, "你好")

    page_hints = {
        "dashboard": "这是数据概览页面，可以查看任务进度和统计。",
        "tasks": "这是任务中心，可以管理批改任务。",
        "ai_generator": "这里可以上传试卷和标准答案，生成 AI 批改核心。",
        "student_list": "这里管理学生名单，支持 Excel 导入。",
        "export": "这里可以导出成绩报表。",
        "library": "这是文档库，管理试卷和教学资料。"
    }

    hint = page_hints.get(page_context, "")

    return f"""为 {username} 老师生成一句简短的页面问候语。

当前情况：
- 时间: {weekday} {time_greeting}
- 页面: {page_display}
- 页面功能: {hint}

要求：
1. 20-40 字，一句话
2. 包含时间问候
3. 提及页面功能或给出小建议
4. 语气友好专业
5. 不要引号，直接输出文本

示例：
- {time_greeting}！欢迎来到{page_display}，有什么需要帮忙的吗？
- {weekday}{time_greeting}，{page_display}已准备就绪，开始处理批改任务吧。

请生成:"""


def get_operation_feedback_prompt(
    username: str,
    operation_type: str,
    operation_result: str,
    details: dict
) -> str:
    """
    获取操作反馈提示词

    Args:
        username: 用户名
        operation_type: 操作类型
        operation_result: 操作结果
        details: 操作详情

    Returns:
        提示词
    """
    operation_names = {
        "generate_grader": "生成批改核心",
        "parse_document": "解析文档",
        "export_grades": "导出成绩",
        "import_students": "导入学生名单",
        "create_class": "创建班级"
    }

    operation_name = operation_names.get(operation_type, operation_type)
    result_text = "成功" if operation_result == "success" else "失败"

    # 构建详情描述
    details_str = ""
    if details:
        detail_items = []
        if "grader_name" in details:
            detail_items.append(f"名称: {details['grader_name']}")
        if "question_count" in details:
            detail_items.append(f"题目数: {details['question_count']}")
        if "count" in details:
            detail_items.append(f"数量: {details['count']}")
        if "error" in details:
            detail_items.append(f"错误: {details['error']}")
        if detail_items:
            details_str = "；".join(detail_items)

    next_step_hints = {
        "generate_grader": "下一步可以创建班级并上传学生作业。" if operation_result == "success" else "请检查上传的文件是否正确。",
        "parse_document": "文档已准备就绪。" if operation_result == "success" else "请确保文件格式正确。",
        "export_grades": "文件已准备好下载。" if operation_result == "success" else "请稍后重试。",
        "import_students": "现在可以进行批改了。" if operation_result == "success" else "请检查文件格式。",
        "create_class": "接下来可以导入学生名单。" if operation_result == "success" else "请检查输入信息。"
    }

    next_hint = next_step_hints.get(operation_type, "")

    return f"""为 {username} 老师生成一句操作反馈消息。

操作信息：
- 操作: {operation_name}
- 结果: {result_text}
- 详情: {details_str if details_str else "无"}
- 建议下一步: {next_hint}

要求：
1. 30-60 字
2. 先说结果，再给建议
3. 成功时语气积极鼓励，失败时语气温和并给出解决方向
4. 不要引号，直接输出文本

示例（成功）：
- 太棒了！批改核心已生成完成，现在可以创建班级开始批改了。
- 学生名单导入成功，共 45 人。准备开始布置作业吧！

示例（失败）：
- 批改核心生成遇到问题，请检查上传的试卷格式是否支持。
- 导入失败了，可能是文件格式不对，试试标准 Excel 模板？

请生成:"""
