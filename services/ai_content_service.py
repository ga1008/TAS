# services/ai_content_service.py
"""
AI 欢迎语内容服务
负责 AI 欢迎语生成、缓存管理和内容验证
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

import httpx

from config import Config
from extensions import db
from services.ai_prompts import (
    PageContext,
    get_fallback_message,
    get_time_period_chinese,
    get_weekday_chinese,
    get_page_context_display,
    PAGE_SPECIFIC_PROMPTS
)

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

@dataclass
class WelcomeMessage:
    """缓存的 AI 欢迎消息数据模型"""
    id: int
    user_id: int
    page_context: str
    message_content: str
    created_at: datetime
    expires_at: datetime
    context_snapshot: Optional[Dict[str, Any]] = None

    @property
    def is_expired(self) -> bool:
        """检查缓存的欢迎语是否已过期"""
        return datetime.now() > self.expires_at

    @property
    def storage_key(self) -> str:
        """生成 localStorage 键名，用于前端跟踪已查看的消息"""
        return f"ai_welcome_seen_{self.page_context}_{self.id}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典用于 JSON 序列化"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'page_context': self.page_context,
            'message_content': self.message_content,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'storage_key': self.storage_key,
            'is_new': True  # 前端用于判断是否显示动画
        }

    @classmethod
    def from_row(cls, row) -> 'WelcomeMessage':
        """从数据库行创建对象"""
        snapshot = None
        if row.get('context_snapshot'):
            try:
                snapshot = json.loads(row['context_snapshot'])
            except json.JSONDecodeError:
                pass

        return cls(
            id=row['id'],
            user_id=row['user_id'],
            page_context=row['page_context'],
            message_content=row['message_content'],
            created_at=datetime.fromisoformat(row['created_at']),
            expires_at=datetime.fromisoformat(row['expires_at']),
            context_snapshot=snapshot
        )


@dataclass
class MessageContext:
    """发送给 AI 的上下文数据"""
    # 用户信息
    username: str

    # 时间上下文
    current_time: str  # HH:MM 格式
    weekday: str  # 中文星期 (周一, 周二, etc.)
    time_period: str  # early_morning, morning, afternoon, evening, night

    # 系统统计
    class_count: int
    student_count: int
    pending_task_count: int
    grader_count: int
    file_count: int

    # 最近操作 (最后 3-5 条)
    recent_actions: List[str]

    # 页面上下文
    page_context: str  # dashboard, tasks, student_list, ai_generator, export

    def to_prompt_dict(self) -> Dict[str, Any]:
        """转换为字典用于 AI 提示词格式化"""
        recent_actions_str = "、".join(self.recent_actions) if self.recent_actions else "暂无"

        # page_context_enum = PageContext(self.page_context) if isinstance(self.page_context, str) else self.page_context

        return {
            'username': self.username,
            'current_time': self.current_time,
            'weekday': self.weekday,
            'time_period': self.time_period,
            'class_count': self.class_count,
            'student_count': self.student_count,
            'pending_task_count': self.pending_task_count,
            'grader_count': self.grader_count,
            'file_count': self.file_count,
            'recent_actions_str': recent_actions_str,
            'page_context': self.page_context,
            'page_context_display': get_page_context_display(self.page_context)
        }

    @classmethod
    def from_request(cls, user_info: Dict[str, Any], stats: Dict[str, Any],
                     page_context: str, recent_actions: List[str]) -> 'MessageContext':
        """从请求数据创建上下文"""
        now = datetime.now()

        # 确定时间段
        time_period = get_time_period_chinese()

        # 中文星期
        weekday = get_weekday_chinese()

        return cls(
            username=user_info.get('username', '老师'),
            current_time=f"{now.hour:02d}:{now.minute:02d}",
            weekday=weekday,
            time_period=time_period,
            class_count=stats.get('class_count', 0),
            student_count=stats.get('student_count', 0),
            pending_task_count=stats.get('pending_task_count', 0),
            grader_count=stats.get('grader_count', 0),
            file_count=stats.get('file_count', 0),
            recent_actions=recent_actions[:5],  # 最多 5 条
            page_context=page_context
        )

    def to_snapshot(self) -> str:
        """转换为 JSON 用于数据库存储"""
        return json.dumps({
            'username': self.username,
            'time_period': self.time_period,
            'class_count': self.class_count,
            'pending_task_count': self.pending_task_count,
            'recent_actions': self.recent_actions
        }, ensure_ascii=False)


# ==================== 内容验证 ====================

def validate_message_content(content: str) -> Tuple[bool, Optional[str]]:
    """
    验证 AI 生成的欢迎语内容

    Args:
        content: 待验证的欢迎语文本

    Returns:
        (是否有效, 错误信息)
    """
    if not content or not content.strip():
        return False, "消息为空"

    content = content.strip()

    # 长度检查
    if not (10 <= len(content) <= 200):
        return False, f"消息长度应为 10-200 字符，当前为 {len(content)} 字符"

    # 中文字符比例检查 (至少 50%)
    chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    total_chars = len(content)
    if total_chars > 0 and chinese_chars / total_chars < 0.5:
        return False, "消息应包含至少 50% 的中文字符"

    # 检查明显的无效模式
    if re.search(r'[<>{}\\]{2,}', content):
        return False, "消息包含无效字符"

    # 过滤掉可能包含代码块标记的输出
    if content.startswith('```') or content.endswith('```'):
        return False, "消息格式无效"

    return True, None


# ==================== 缓存管理 ====================

def get_cached_message(user_id: int, page_context: str) -> Optional[WelcomeMessage]:
    """
    从缓存获取欢迎语

    Args:
        user_id: 用户 ID
        page_context: 页面上下文

    Returns:
        WelcomeMessage 对象，如果缓存不存在或已过期返回 None
    """
    try:
        conn = db.get_connection()
        row = conn.execute('''
            SELECT * FROM ai_welcome_messages
            WHERE user_id = ? AND page_context = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id, page_context)).fetchone()

        if not row:
            return None
        row = dict(row)
        msg = WelcomeMessage.from_row(row)

        # 检查是否过期
        if msg.is_expired:
            logger.debug(f"缓存消息已过期: user_id={user_id}, page_context={page_context}")
            return None

        return msg

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"获取缓存消息失败: {e}")
        return None


def save_to_cache(user_id: int, page_context: str, message_content: str,
                  context: MessageContext, ttl_seconds: int = None) -> WelcomeMessage:
    """
    保存欢迎语到缓存

    Args:
        user_id: 用户 ID
        page_context: 页面上下文
        message_content: 欢迎语内容
        context: 生成时的上下文
        ttl_seconds: 缓存 TTL（秒），默认从配置读取

    Returns:
        保存的 WelcomeMessage 对象
    """
    if ttl_seconds is None:
        ttl_seconds = Config.AI_WELCOME_CACHE_TTL

    now = datetime.now()
    expires_at = now + timedelta(seconds=ttl_seconds)

    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO ai_welcome_messages
        (user_id, page_context, message_content, created_at, expires_at, context_snapshot)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        page_context,
        message_content,
        now.isoformat(),
        expires_at.isoformat(),
        context.to_snapshot()
    ))
    conn.commit()

    msg_id = cursor.lastrowid
    logger.info(f"缓存欢迎语已保存: user_id={user_id}, page_context={page_context}, msg_id={msg_id}")

    return WelcomeMessage(
        id=msg_id,
        user_id=user_id,
        page_context=page_context,
        message_content=message_content,
        created_at=now,
        expires_at=expires_at,
        context_snapshot=context.to_prompt_dict()
    )


def invalidate_cache(user_id: int, page_context: str = None) -> bool:
    """
    使缓存失效

    Args:
        user_id: 用户 ID
        page_context: 页面上下文，如果为 None 则清除该用户的所有缓存

    Returns:
        是否成功
    """
    try:
        conn = db.get_connection()
        if page_context:
            conn.execute('''
                DELETE FROM ai_welcome_messages
                WHERE user_id = ? AND page_context = ?
            ''', (user_id, page_context))
            logger.info(f"缓存已失效: user_id={user_id}, page_context={page_context}")
        else:
            conn.execute('''
                DELETE FROM ai_welcome_messages
                WHERE user_id = ?
            ''', (user_id,))
            logger.info(f"用户所有缓存已失效: user_id={user_id}")
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"缓存失效失败: {e}")
        return False


def cleanup_expired_messages() -> int:
    """
    清理过期的欢迎语缓存

    Returns:
        清理的记录数
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM ai_welcome_messages
            WHERE expires_at < ?
        ''', (datetime.now().isoformat(),))
        conn.commit()
        count = cursor.rowcount
        if count > 0:
            logger.info(f"清理了 {count} 条过期缓存")
        return count
    except Exception as e:
        logger.error(f"清理过期缓存失败: {e}")
        return 0


# ==================== AI 生成 ====================

async def generate_welcome_message(
    user_id: int,
    page_context: str,
    user_info: Dict[str, Any],
    stats: Dict[str, Any],
    recent_actions: List[str],
    force_refresh: bool = False,
    extra_context: Dict[str, Any] = None
) -> Tuple[Optional[WelcomeMessage], str]:
    """
    生成或获取欢迎语

    Args:
        user_id: 用户 ID
        page_context: 页面上下文
        user_info: 用户信息
        stats: 统计数据
        recent_actions: 最近操作列表
        force_refresh: 是否强制刷新（忽略缓存）

    Returns:
        (WelcomeMessage, status) 元组
        status 可能的值: 'cached', 'generated', 'fallback'
    """
    # 如果不强制刷新，先尝试从缓存获取
    if not force_refresh:
        cached = get_cached_message(user_id, page_context)
        if cached:
            logger.debug(f"使用缓存的欢迎语: user_id={user_id}, page_context={page_context}")
            return cached, 'cached'

    # 构建上下文
    context = MessageContext.from_request(user_info, stats, page_context, recent_actions)

    # 选择合适的提示词模板
    try:
        page_enum = PageContext(page_context)
        prompt_template = PAGE_SPECIFIC_PROMPTS.get(page_enum, PAGE_SPECIFIC_PROMPTS[PageContext.DASHBOARD])
    except ValueError:
        prompt_template = PAGE_SPECIFIC_PROMPTS[PageContext.DASHBOARD]

    # 格式化提示词
    prompt_vars = context.to_prompt_dict()

    # 合并 extra_context (用于 trigger_reason, action_details 等)
    if extra_context:
        prompt_vars.update(extra_context)

    # 确保所有必需的模板变量都有默认值
    prompt_vars.setdefault('trigger_reason', 'timer')
    prompt_vars.setdefault('action_details', '')
    prompt_vars.setdefault('last_action_desc', '无')
    prompt_vars.setdefault('last_action', prompt_vars.get('recent_actions_str', '无'))

    full_prompt = prompt_template.format(**prompt_vars)

    # 调用 AI 生成
    try:
        ai_content = await _call_ai_for_welcome(full_prompt)

        # 验证生成的内容
        is_valid, error_msg = validate_message_content(ai_content)
        if not is_valid:
            logger.warning(f"AI 生成内容验证失败: {error_msg}, 使用回退消息")
            fallback_msg = get_fallback_message(context.time_period)
            saved_msg = save_to_cache(user_id, page_context, fallback_msg, context, ttl_seconds=3600)
            return saved_msg, 'fallback'

        # 保存到缓存
        saved_msg = save_to_cache(user_id, page_context, ai_content, context)
        return saved_msg, 'generated'

    except RateLimitError as e:
        # 速率限制时，尝试使用旧缓存（即使过期）
        logger.warning(f"AI 服务速率受限: {e}，尝试使用旧缓存")
        stale_cached = get_cached_message(user_id, page_context)
        if stale_cached:
            # 延长旧缓存的有效期
            from datetime import timedelta
            stale_cached.expires_at = datetime.now() + timedelta(hours=1)
            return stale_cached, 'cached'

        # 没有旧缓存，使用回退消息
        fallback_msg = get_fallback_message(context.time_period)
        saved_msg = save_to_cache(user_id, page_context, fallback_msg, context, ttl_seconds=3600)
        return saved_msg, 'fallback'

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"AI 生成欢迎语失败: {e}")
        # 使用回退消息
        fallback_msg = get_fallback_message(context.time_period)
        saved_msg = save_to_cache(user_id, page_context, fallback_msg, context, ttl_seconds=3600)
        return saved_msg, 'fallback'


async def _call_ai_for_welcome(prompt: str) -> str:
    """
    调用 AI 服务生成欢迎语

    Args:
        prompt: 格式化后的提示词

    Returns:
        AI 生成的欢迎语文本

    Raises:
        Exception: 当 AI 服务不可用或返回错误时
    """
    # 获取 AI 配置
    config = db.get_best_ai_config("standard")
    if not config:
        raise Exception("没有可用的 AI 配置")

    endpoint = Config.AI_ASSISTANT_CHAT_ENDPOINT

    payload = {
        "system_prompt": "你是一个智能教学助手的欢迎语生成器。请直接输出欢迎语文本，不要有任何多余的解释或标记。",
        "messages": [],
        "new_message": prompt,
        "model_capability": "standard"
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, json=payload)

        # 处理速率限制 (HTTP 429)
        if response.status_code == 429:
            logger.warning("AI 服务速率限制 (429)，将使用回退消息")
            raise RateLimitError("AI 服务速率限制")

        if response.status_code != 200:
            logger.error(f"AI 服务返回错误: {response.status_code}")
            raise Exception(f"AI 服务返回错误: {response.status_code}")

        data = response.json()
        content = data.get("response_text", "").strip()

        # 清理可能的代码块标记
        if content.startswith("```"):
            content = re.sub(r'^```[a-z]*\n?', '', content)
        if content.endswith("```"):
            content = re.sub(r'\n?```$', '', content)

        return content


class RateLimitError(Exception):
    """速率限制异常"""
    pass


def get_fallback_message_sync(time_period: str = None) -> str:
    """
    同步获取回退欢迎语

    Args:
        time_period: 时间段

    Returns:
        回退欢迎语
    """
    return get_fallback_message(time_period)


# ==================== AI 对话助手 (Feature 002) ====================

async def call_ai_for_conversation(
    user_info: Dict[str, Any],
    messages: List,
    page_context: str = None
) -> str:
    """
    调用 AI 进行多轮对话

    Args:
        user_info: 用户信息
        messages: 历史消息列表 (Message 对象列表)
        page_context: 当前页面上下文

    Returns:
        AI 回复内容
    """
    from services.ai_prompts import get_conversation_system_prompt

    # 获取 AI 配置
    config = db.get_best_ai_config("standard")
    if not config:
        raise Exception("没有可用的 AI 配置")

    # 构建系统提示词
    system_prompt = get_conversation_system_prompt(
        username=user_info.get('username', '老师'),
        page_context=page_context
    )

    # 构建消息历史
    message_history = []
    for msg in messages:
        role = msg.role if hasattr(msg, 'role') else msg.get('role', 'user')
        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
        if role in ['user', 'assistant']:
            message_history.append({
                'role': role,
                'content': content
            })

    endpoint = Config.AI_ASSISTANT_CHAT_ENDPOINT

    # 取最后一条用户消息作为 new_message
    new_message = ""
    if message_history and message_history[-1]['role'] == 'user':
        new_message = message_history[-1]['content']
        message_history = message_history[:-1]  # 移除最后一条

    payload = {
        "system_prompt": system_prompt,
        "messages": message_history,
        "new_message": new_message,
        "model_capability": "standard"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(endpoint, json=payload)

        if response.status_code == 429:
            raise RateLimitError("AI 服务速率限制")

        if response.status_code != 200:
            raise Exception(f"AI 服务返回错误: {response.status_code}")

        data = response.json()
        content = data.get("response_text", "").strip()

        # 清理可能的代码块标记
        if content.startswith("```"):
            content = re.sub(r'^```[a-z]*\n?', '', content)
        if content.endswith("```"):
            content = re.sub(r'\n?```$', '', content)

        return content if content else "抱歉，我暂时无法回复。请稍后再试。"


async def generate_page_greeting(
    user_info: Dict[str, Any],
    page_context: str
) -> str:
    """
    生成页面切换时的问候语

    Args:
        user_info: 用户信息
        page_context: 页面上下文

    Returns:
        问候语内容
    """
    from services.ai_prompts import get_page_greeting_prompt

    # 获取 AI 配置
    config = db.get_best_ai_config("standard")
    if not config:
        # 使用回退消息
        return _get_page_greeting_fallback(page_context)

    prompt = get_page_greeting_prompt(
        username=user_info.get('username', '老师'),
        page_context=page_context
    )

    endpoint = Config.AI_ASSISTANT_CHAT_ENDPOINT

    payload = {
        "system_prompt": "你是一个智能教学助手。请用简洁友好的语气生成问候语。",
        "messages": [],
        "new_message": prompt,
        "model_capability": "standard"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, json=payload)

            if response.status_code != 200:
                return _get_page_greeting_fallback(page_context)

            data = response.json()
            content = data.get("response_text", "").strip()

            # 验证内容
            is_valid, _ = validate_message_content(content)
            if not is_valid:
                return _get_page_greeting_fallback(page_context)

            return content

    except Exception as e:
        logger.error(f"生成页面问候失败: {e}")
        return _get_page_greeting_fallback(page_context)


def _get_page_greeting_fallback(page_context: str) -> str:
    """页面问候的回退消息"""
    greetings = {
        'dashboard': '欢迎回来！这是您的仪表板，可以查看整体数据概览。',
        'tasks': '这是任务中心，您可以在这里管理批改任务。',
        'ai_generator': '欢迎来到 AI 生成页面！上传试卷和评分标准即可生成批改核心。',
        'export': '这是导出中心，您可以导出成绩和报告。',
        'student_list': '这是学生名单管理页面，可以导入和管理学生信息。',
        'library': '这是文档库，您可以在这里管理试卷和资料。'
    }
    return greetings.get(page_context, '有什么我可以帮您的吗？')


async def generate_operation_feedback(
    user_info: Dict[str, Any],
    operation_type: str,
    operation_result: str,
    details: Dict[str, Any] = None
) -> str:
    """
    生成操作完成后的反馈消息

    Args:
        user_info: 用户信息
        operation_type: 操作类型
        operation_result: 操作结果 (success/error)
        details: 操作详情

    Returns:
        反馈消息内容
    """
    from services.ai_prompts import get_operation_feedback_prompt

    # 获取 AI 配置
    config = db.get_best_ai_config("standard")
    if not config:
        return _get_operation_feedback_fallback(operation_type, operation_result, details)

    prompt = get_operation_feedback_prompt(
        username=user_info.get('username', '老师'),
        operation_type=operation_type,
        operation_result=operation_result,
        details=details or {}
    )

    endpoint = Config.AI_ASSISTANT_CHAT_ENDPOINT

    payload = {
        "system_prompt": "你是一个智能教学助手。请用简洁友好的语气反馈操作结果，并给出下一步建议。",
        "messages": [],
        "new_message": prompt,
        "model_capability": "standard"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, json=payload)

            if response.status_code != 200:
                return _get_operation_feedback_fallback(operation_type, operation_result, details)

            data = response.json()
            content = data.get("response_text", "").strip()

            # 验证内容
            is_valid, _ = validate_message_content(content)
            if not is_valid:
                return _get_operation_feedback_fallback(operation_type, operation_result, details)

            return content

    except Exception as e:
        logger.error(f"生成操作反馈失败: {e}")
        return _get_operation_feedback_fallback(operation_type, operation_result, details)


def _get_operation_feedback_fallback(
    operation_type: str,
    operation_result: str,
    details: Dict[str, Any] = None
) -> str:
    """操作反馈的回退消息"""
    details = details or {}

    if operation_result == 'success':
        feedbacks = {
            'generate_grader': f"批改核心已成功生成！现在可以创建班级并上传学生作业进行批改了。",
            'parse_document': "文档解析完成！您可以在文档库中查看解析结果。",
            'export_grades': "成绩导出成功！文件已准备好下载。",
            'import_students': f"学生名单导入成功！共导入 {details.get('count', '若干')} 名学生。",
            'create_class': f"班级创建成功！现在可以导入学生名单了。"
        }
    else:
        feedbacks = {
            'generate_grader': "批改核心生成失败，请检查上传的文件格式是否正确。",
            'parse_document': "文档解析失败，请确保文件格式支持且内容清晰。",
            'export_grades': "成绩导出失败，请稍后重试。",
            'import_students': "学生名单导入失败，请检查文件格式。",
            'create_class': "班级创建失败，请检查输入信息。"
        }

    return feedbacks.get(operation_type, '操作已完成。' if operation_result == 'success' else '操作失败，请重试。')
