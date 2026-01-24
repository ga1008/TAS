# blueprints/ai_welcome.py
"""
AI 欢迎语蓝图 (Reborn)
提供基于场景、时间和用户行为的智能欢迎语及对话 API
"""

import asyncio
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, g

from extensions import db
from services.ai_conversation_service import AIConversationService
from services.ai_content_service import (
    generate_welcome_message,
    get_fallback_message_sync
)
from services.ai_prompts import get_conversation_system_prompt
from ai_utils.ai_helper import call_ai_platform_chat

bp = Blueprint('ai_welcome', __name__)
logger = logging.getLogger(__name__)


def get_user_stats(user_id: int) -> dict:
    """获取用户统计数据 (用于填充 Prompt)"""
    conn = db.get_connection()

    # 获取班级数
    class_count_row = conn.execute(
        'SELECT COUNT(*) as count FROM classes WHERE created_by=?',
        (user_id,)
    ).fetchone()
    class_count = class_count_row['count'] if class_count_row else 0

    # 获取学生总数
    student_count_row = conn.execute('''
                                     SELECT COUNT(DISTINCT s.student_id) as count
                                     FROM students s
                                              JOIN classes c ON s.class_id = c.id
                                     WHERE c.created_by = ?
                                     ''', (user_id,)).fetchone()
    student_count = student_count_row['count'] if student_count_row else 0

    # 获取评分核心数
    grader_count_row = conn.execute(
        'SELECT COUNT(*) as count FROM ai_tasks WHERE created_by=? AND grader_id IS NOT NULL',
        (user_id,)
    ).fetchone()
    grader_count = grader_count_row['count'] if grader_count_row else 0

    # 获取待处理任务数
    pending_count_row = conn.execute('''
                                     SELECT COUNT(*) as count
                                     FROM ai_tasks
                                     WHERE created_by = ?
                                       AND status IN ('pending', 'processing')
                                     ''', (user_id,)).fetchone()
    pending_count = pending_count_row['count'] if pending_count_row else 0

    # 获取已上传文件数
    file_count_row = conn.execute(
        'SELECT COUNT(*) as count FROM file_assets WHERE uploaded_by=?',
        (user_id,)
    ).fetchone()
    file_count = file_count_row['count'] if file_count_row else 0

    return {
        'class_count': class_count,
        'student_count': student_count,
        'grader_count': grader_count,
        'pending_task_count': pending_count,
        'file_count': file_count
    }


def get_recent_actions(user_id: int, limit: int = 3) -> list:
    """获取用户最近的操作 (用于 AI 吐槽)"""
    conn = db.get_connection()
    all_actions = []

    # 1. 班级
    for item in conn.execute('SELECT name, created_at FROM classes WHERE created_by=? ORDER BY created_at DESC LIMIT ?',
                             (user_id, limit)).fetchall():
        all_actions.append({'desc': f"创建班级 {item['name']}", 'time': item['created_at']})

    # 2. 评分核心
    for item in conn.execute(
            'SELECT name, created_at FROM ai_tasks WHERE created_by=? AND grader_id IS NOT NULL ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)).fetchall():
        all_actions.append({'desc': f"生成核心 {item['name']}", 'time': item['created_at']})

    # 3. 文件
    for item in conn.execute(
            'SELECT original_name, created_at FROM file_assets WHERE uploaded_by=? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)).fetchall():
        all_actions.append({'desc': f"上传文件 {item['original_name']}", 'time': item['created_at']})

    all_actions.sort(key=lambda x: x['time'], reverse=True)
    return [action['desc'] for action in all_actions[:limit]]


@bp.route('/api/welcome/messages', methods=['POST'])
def get_welcome_message():
    """
    获取 AI 欢迎语/主动提示 (主入口)

    JSON Params:
        page_context: 当前页面标识
        trigger_type: 'timer' | 'action'
        action_details: 操作详情字符串 (仅 action 类型有效)
    """
    if 'user' not in g or not g.user:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    user_id = g.user['id']
    data = request.get_json() or {}

    page_context = data.get('page_context', 'dashboard')
    trigger_type = data.get('trigger_type', 'timer')
    action_details = data.get('action_details', '')

    # 初始化服务
    conversation_service = AIConversationService(db)

    # 1. 速率限制检查
    # Timer 触发：60秒冷却；Action 触发：10秒冷却
    cooldown = 60 if trigger_type == 'timer' else 10
    allowed, remaining = conversation_service.check_rate_limit(user_id, cooldown_seconds=cooldown)

    if not allowed:
        return jsonify({'status': 'silence', 'message': f'Rate limited. Try again in {remaining}s'})

    try:
        # 获取上下文数据
        stats = get_user_stats(user_id)
        recent_actions = get_recent_actions(user_id)

        # 记录本次触发时间 (Token消耗控制)
        conversation_service.update_rate_limit(user_id)

        # 2. 调用 AI 生成
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            extra_context = {
                "trigger_reason": trigger_type,
                "action_details": action_details,
                "last_action_desc": recent_actions[0] if recent_actions else "无"
            }

            message, status = loop.run_until_complete(
                generate_welcome_message(
                    user_id=user_id,
                    page_context=page_context,
                    user_info=g.user,
                    stats=stats,
                    recent_actions=recent_actions,
                    force_refresh=True,  # 主动触发强制刷新
                    extra_context=extra_context
                )
            )
        finally:
            loop.close()

        if message:
            return jsonify({
                'status': 'success',
                'data': message.to_dict()
            })
        else:
            fallback = get_fallback_message_sync()
            return jsonify({
                'status': 'fallback',
                'data': {'message_content': fallback}
            })

    except Exception as e:
        logger.error(f"获取欢迎语失败: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/api/welcome/chat', methods=['POST'])
def chat_with_assistant():
    """
    用户手动与助手对话接口

    JSON Params:
        message: 用户发送的内容
        page_context: 当前页面
    """
    if 'user' not in g or not g.user:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    user_id = g.user['id']
    username = g.user.get('username', 'Teacher')
    data = request.get_json() or {}
    user_message_content = data.get('message', '').strip()
    page_context = data.get('page_context', 'dashboard')

    if not user_message_content:
        return jsonify({'status': 'error', 'message': '内容不能为空'}), 400

    conversation_service = AIConversationService(db)

    try:
        # 1. 获取或创建活跃会话
        conversation = conversation_service.get_active_conversation(user_id)

        # 2. 保存用户消息
        conversation_service.add_message(
            conversation_id=conversation.id,
            role='user',
            content=user_message_content,
            metadata={'page_context': page_context}
        )

        # 3. 准备 AI 上下文
        # 获取最近 10 条历史消息
        history_msgs = conversation_service.get_recent_messages(conversation.id, limit=10)

        # 转换消息格式适配 AI 接口
        ai_messages = []
        for msg in history_msgs:
            ai_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 获取系统设定 Prompt ("互联网嘴替"人设)
        system_prompt = get_conversation_system_prompt(username, page_context)

        # 4. 调用 AI (使用 asyncio 运行异步任务)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # 获取配置 (优先使用 chat 或 thinking 能力的模型)
            # 这里简化逻辑，直接取 thinking 或 standard
            config = db.get_best_ai_config('thinking') or db.get_best_ai_config('standard')

            if not config:
                response_text = "抱歉，AI 服务暂时不可用（未配置模型）。"
            else:
                response_text = loop.run_until_complete(
                    call_ai_platform_chat(
                        system_prompt=system_prompt,
                        messages=ai_messages,
                        platform_config=config
                    )
                )
        finally:
            loop.close()

        # 5. 保存 AI 回复
        if not response_text:
            response_text = "（AI 似乎在思考人生，没有返回内容...）"

        conversation_service.add_message(
            conversation_id=conversation.id,
            role='assistant',
            content=response_text
        )

        return jsonify({
            'status': 'success',
            'data': {
                'reply': response_text,
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"对话失败: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'AI 暂时掉线了'}), 500


@bp.route('/api/welcome/fallback', methods=['GET'])
def get_fallback():
    """获取静态回退消息 (无需登录)"""
    try:
        message = get_fallback_message_sync()
        return jsonify({'status': 'success', 'data': {'message': message}})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def cleanup_old_welcome_messages(days: int = 30) -> int:
    """
    清理超过指定天数的欢迎语记录

    Args:
        days: 保留的天数，默认 30 天

    Returns:
        清理的记录数
    """
    try:
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        conn = db.get_connection()
        cursor = conn.cursor()

        # 清理 ai_welcome_messages 表
        cursor.execute('''
            DELETE FROM ai_welcome_messages
            WHERE created_at < ?
        ''', (cutoff_date,))
        welcome_count = cursor.rowcount

        # 清理 ai_rate_limits 表中的旧记录
        cursor.execute('''
            DELETE FROM ai_rate_limits
            WHERE last_request_time < ?
        ''', (cutoff_date,))
        rate_count = cursor.rowcount

        conn.commit()

        total = welcome_count + rate_count
        if total > 0:
            logger.info(f"[AI Welcome] 清理了 {welcome_count} 条欢迎语和 {rate_count} 条速率限制记录 (超过 {days} 天)")

        return total

    except Exception as e:
        logger.error(f"清理旧欢迎语记录失败: {e}")
        return 0