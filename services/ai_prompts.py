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

WELCOME_PROMPT_TEMPLATE = """你是一个智能教学助手的欢迎语生成器。请根据用户信息生成一条个性化、温暖且有指导意义的欢迎语。

### 输出要求
1. 只输出欢迎语文本，不要有引号、不要有 markdown 标记
2. 长度控制在 15-60 个中文字符
3. 语气要温暖、鼓励、专业
4. 根据当前时间和用户状态给出恰当的问候和建议

### 用户信息
- 用户名: {username}
- 当前时间: {current_time}
- 星期: {weekday}
- 时段: {time_period}
- 批改任务数: {class_count}
- 学生总数: {student_count}
- 待处理任务数: {pending_task_count}
- 已生成评分核心数: {grader_count}
- 最近操作: {recent_actions_str}

### 页面上下文
当前页面: {page_context_display}

### 参考示例 (根据不同场景)

**早晨 (6-11点) 问候示例:**
- 早安，新的一天开始了！您有 {class_count} 个批改任务待处理，加油！
- 早上好，{username}老师！今天是个高效工作日，开始批改吧。

**下午 (12-17点) 问候示例:**
- 下午好，保持专注！您还有 {pending_task_count} 个任务待完成。
- 下午时段，适合批量批改。您已生成 {grader_count} 个评分核心，继续努力！

**晚上 (18-22点) 问候示例:**
- 晚上好，今天辛苦了！离目标又近了一步。
- 继续加油，您即将完成所有批改任务！

**深夜 (23-5点) 问候示例:**
- 夜深了，注意休息。明天继续高效工作！

### 根据用户状态的个性化建议
- 无任务时: 鼓励创建新任务
- 有待处理任务时: 鼓励开始批改
- 批改进度良好时: 肯定成果
- 刚生成评分核心时: 建议导入学生名单

请现在生成一条欢迎语:
"""


# 页面特定的提示词扩展
PAGE_SPECIFIC_PROMPTS = {
    PageContext.DASHBOARD: WELCOME_PROMPT_TEMPLATE,

    PageContext.TASKS: """你是一个智能教学助手的任务列表页欢迎语生成器。

### 用户信息
- 用户名: {username}
- 当前时间: {current_time}
- 星期: {weekday}
- 时段: {time_period}
- 批改任务数: {class_count}
- 待处理任务数: {pending_task_count}

### 输出要求
1. 只输出欢迎语文本，不要有引号
2. 长度控制在 15-50 个中文字符
3. 重点关注任务处理建议

### 参考示例
- 这里是您的批改任务列表，共 {class_count} 个班级。
- 您有 {pending_task_count} 个任务正在进行中，继续加油！

请生成一条任务页欢迎语:
""",

    PageContext.STUDENT_LIST: """你是一个智能教学助手的学生列表页欢迎语生成器。

### 用户信息
- 用户名: {username}
- 学生总数: {student_count}

### 输出要求
1. 只输出欢迎语文本，不要有引号
2. 长度控制在 15-40 个中文字符
3. 重点关注学生管理建议

### 参考示例
- 您已导入 {student_count} 名学生，可以开始批改了。
- 学生名单准备就绪，共 {student_count} 人。

请生成一条学生列表页欢迎语:
""",

    PageContext.AI_GENERATOR: """你是一个智能教学助手的 AI 生成器页欢迎语生成器。

### 用户信息
- 用户名: {username}
- 已生成核心数: {grader_count}

### 输出要求
1. 只输出欢迎语文本，不要有引号
2. 长度控制在 15-40 个中文字符
3. 重点关注 AI 批改核心生成建议

### 参考示例
- 已为您生成 {grader_count} 个评分核心，继续创建更多吧！
- 上传试卷和评分标准，AI 帮您自动生成批改脚本。

请生成一条 AI 生成器页欢迎语:
""",

    PageContext.EXPORT: """你是一个智能教学助手的导出页欢迎语生成器。

### 用户信息
- 用户名: {username}
- 批改任务数: {class_count}

### 输出要求
1. 只输出欢迎语文本，不要有引号
2. 长度控制在 15-40 个中文字符
3. 重点关注成绩导出建议

### 参考示例
- 您有 {class_count} 个班级的成绩可以导出。
- 批改完成后，可以一键导出成绩单。

请生成一条导出页欢迎语:
""",
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
