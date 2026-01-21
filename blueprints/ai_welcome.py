# blueprints/ai_welcome.py
"""
AI 欢迎语蓝图
提供欢迎语相关的 API 端点
"""

import asyncio
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, g

from extensions import db
from services.ai_content_service import (
    generate_welcome_message,
    get_fallback_message_sync,
    invalidate_cache,
    cleanup_expired_messages
)

bp = Blueprint('ai_welcome', __name__)
logger = logging.getLogger(__name__)


def get_user_stats(user_id: int) -> dict:
    """
    获取用户统计数据

    Args:
        user_id: 用户 ID

    Returns:
        统计数据字典
    """
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
        WHERE created_by = ? AND status IN ('pending', 'processing')
    ''', (user_id,)).fetchone()
    pending_count = pending_count_row['count'] if pending_count_row else 0

    return {
        'class_count': class_count,
        'student_count': student_count,
        'grader_count': grader_count,
        'pending_task_count': pending_count
    }


def get_recent_actions(user_id: int, limit: int = 5) -> list:
    """
    获取用户最近的操作

    Args:
        user_id: 用户 ID
        limit: 返回数量限制

    Returns:
        最近操作列表
    """
    conn = db.get_connection()
    actions = []

    # 获取最近创建的班级
    recent_classes = conn.execute('''
        SELECT name, created_at
        FROM classes
        WHERE created_by = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, 3)).fetchall()

    for cls in recent_classes:
        actions.append(f"创建班级 {cls['name']}")

    # 获取最近生成的评分核心
    recent_graders = conn.execute('''
        SELECT name, created_at
        FROM ai_tasks
        WHERE created_by = ? AND grader_id IS NOT NULL
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, 2)).fetchone()

    if recent_graders:
        actions.append(f"生成评分核心 {recent_graders['name']}")

    return actions[:limit]


@bp.route('/api/welcome/messages', methods=['GET'])
def get_welcome_message():
    """
    获取欢迎语

    Query Params:
        page_context: 页面上下文 (dashboard, tasks, student_list, ai_generator, export)
                      默认为 dashboard

    Returns:
        JSON 响应，包含欢迎语数据
    """
    if 'user' not in g or not g.user:
        return jsonify({
            'status': 'error',
            'message': '请先登录'
        }), 401

    user_id = g.user['id']
    page_context = request.args.get('page_context', 'dashboard')

    # 验证 page_context
    valid_contexts = ['dashboard', 'tasks', 'student_list', 'ai_generator', 'export']
    if page_context not in valid_contexts:
        page_context = 'dashboard'

    force_refresh = request.args.get('refresh', 'false').lower() == 'true'

    try:
        # 获取用户统计
        stats = get_user_stats(user_id)

        # 获取最近操作
        recent_actions = get_recent_actions(user_id)

        # 生成欢迎语
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            message, status = loop.run_until_complete(
                generate_welcome_message(
                    user_id=user_id,
                    page_context=page_context,
                    user_info=g.user,
                    stats=stats,
                    recent_actions=recent_actions,
                    force_refresh=force_refresh
                )
            )
        finally:
            loop.close()

        if message:
            return jsonify({
                'status': 'success' if status in ['cached', 'generated'] else 'fallback',
                'data': message.to_dict()
            })
        else:
            # 完全失败，返回默认回退消息
            fallback = get_fallback_message_sync()
            return jsonify({
                'status': 'fallback',
                'data': {
                    'message_content': fallback,
                    'storage_key': f"ai_welcome_seen_{page_context}_fallback_{int(datetime.now().timestamp())}"
                }
            })

    except Exception as e:
        logger.error(f"获取欢迎语失败: {e}")
        # 返回回退消息
        fallback = get_fallback_message_sync()
        return jsonify({
            'status': 'fallback',
            'data': {
                'message_content': fallback,
                'storage_key': f"ai_welcome_seen_{page_context}_fallback_{int(datetime.now().timestamp())}"
            }
        })


@bp.route('/api/welcome/messages/refresh', methods=['POST'])
def refresh_welcome_message():
    """
    刷新欢迎语（强制重新生成）

    Query Params:
        page_context: 页面上下文，默认为 dashboard

    Returns:
        JSON 响应，包含新生成的欢迎语数据
    """
    if 'user' not in g or not g.user:
        return jsonify({
            'status': 'error',
            'message': '请先登录'
        }), 401

    user_id = g.user['id']
    page_context = request.args.get('page_context', 'dashboard')

    # 验证 page_context
    valid_contexts = ['dashboard', 'tasks', 'student_list', 'ai_generator', 'export']
    if page_context not in valid_contexts:
        page_context = 'dashboard'

    try:
        # 先使缓存失效
        invalidate_cache(user_id, page_context)

        # 获取用户统计
        stats = get_user_stats(user_id)

        # 获取最近操作
        recent_actions = get_recent_actions(user_id)

        # 生成新欢迎语
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            message, status = loop.run_until_complete(
                generate_welcome_message(
                    user_id=user_id,
                    page_context=page_context,
                    user_info=g.user,
                    stats=stats,
                    recent_actions=recent_actions,
                    force_refresh=True
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
                'data': {
                    'message_content': fallback,
                    'storage_key': f"ai_welcome_seen_{page_context}_fallback_{int(datetime.now().timestamp())}"
                }
            })

    except Exception as e:
        logger.error(f"刷新欢迎语失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'刷新失败: {str(e)}'
        }), 500


@bp.route('/api/welcome/fallback', methods=['GET'])
def get_fallback():
    """
    获取基于时间的回退欢迎语（无需登录）

    Query Params:
        time_of_day: 时间段 (morning, afternoon, evening, night)
                    如果不提供，则自动检测当前时间

    Returns:
        JSON 响应，包含回退欢迎语
    """
    time_period = request.args.get('time_of_day')

    try:
        message = get_fallback_message_sync(time_period)

        # 确定实际使用的时间段
        if not time_period:
            from services.ai_prompts import get_time_period_chinese
            time_period = get_time_period_chinese()

        return jsonify({
            'status': 'success',
            'data': {
                'message': message,
                'time_period': time_period
            }
        })

    except Exception as e:
        logger.error(f"获取回退欢迎语失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
