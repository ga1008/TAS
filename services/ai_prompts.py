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
        "export": "成绩导出"
    }
    return display_map.get(page_context, "工作台")
