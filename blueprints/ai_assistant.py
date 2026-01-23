# blueprints/ai_assistant.py
"""
AI 助手蓝图
提供全局 AI 助手的 API 端点

Feature: 002-global-ai-assistant
"""

import asyncio
import logging
from flask import Blueprint, jsonify, request, g

from extensions import db
from services.ai_conversation_service import AIConversationService

bp = Blueprint('ai_assistant', __name__)
logger = logging.getLogger(__name__)

# 初始化服务
_conversation_service = None


def get_conversation_service() -> AIConversationService:
    """获取对话服务实例（懒加载）"""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = AIConversationService(db)
    return _conversation_service


def require_login():
    """检查用户是否登录"""
    if 'user' not in g or not g.user:
        return jsonify({
            'status': 'error',
            'error': {'code': 'UNAUTHORIZED', 'message': '请先登录'}
        }), 401
    return None


def make_error_response(code: str, message: str, status_code: int = 400, details: dict = None):
    """生成标准错误响应"""
    error = {'code': code, 'message': message}
    if details:
        error['details'] = details
    return jsonify({'status': 'error', 'error': error}), status_code


# ==================== 对话管理端点 ====================

@bp.route('/api/assistant/conversations', methods=['POST'])
def create_conversation():
    """
    创建新对话会话

    Request Body:
        title: 对话标题 (可选，默认 "新对话")

    Returns:
        201: 新创建的对话信息
    """
    auth_error = require_login()
    if auth_error:
        return auth_error

    user_id = g.user['id']
    data = request.get_json() or {}
    title = data.get('title', '新对话')

    try:
        service = get_conversation_service()

        # 创建新对话（之前的活跃对话会自动归档）
        conversation = service.create_conversation(user_id, title)

        return jsonify({
            'status': 'success',
            'data': conversation.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        return make_error_response('INTERNAL_ERROR', f'创建对话失败: {str(e)}', 500)


@bp.route('/api/assistant/conversations/active', methods=['GET'])
def get_active_conversation():
    """
    获取当前活跃会话，如果没有则自动创建一个

    Returns:
        200: 活跃对话信息
    """
    auth_error = require_login()
    if auth_error:
        return auth_error

    user_id = g.user['id']

    try:
        service = get_conversation_service()
        conversation = service.get_active_conversation(user_id)

        return jsonify({
            'status': 'success',
            'data': conversation.to_dict()
        })

    except Exception as e:
        logger.error(f"获取活跃对话失败: {e}")
        return make_error_response('INTERNAL_ERROR', f'获取活跃对话失败: {str(e)}', 500)


@bp.route('/api/assistant/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id: int):
    """
    获取会话消息历史（支持分页）

    Query Params:
        limit: 每页消息数 (1-100, 默认 20)
        offset: 偏移量 (默认 0)
        order: 排序 "asc" / "desc" (默认 "desc")

    Returns:
        200: 消息列表和分页信息
    """
    auth_error = require_login()
    if auth_error:
        return auth_error

    user_id = g.user['id']

    # 解析分页参数
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return make_error_response('INVALID_REQUEST', '分页参数无效', 400)

    order = request.args.get('order', 'desc')
    if order not in ['asc', 'desc']:
        order = 'desc'

    try:
        service = get_conversation_service()

        # 验证会话权限
        conversation = service.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return make_error_response('NOT_FOUND', '会话不存在或无权访问', 404)

        # 获取消息
        messages, total = service.get_messages(conversation_id, limit, offset, order)

        return jsonify({
            'status': 'success',
            'data': {
                'messages': [msg.to_dict() for msg in messages],
                'pagination': {
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + len(messages) < total
                }
            }
        })

    except Exception as e:
        logger.error(f"获取会话消息失败: {e}")
        return make_error_response('INTERNAL_ERROR', f'获取消息失败: {str(e)}', 500)


@bp.route('/api/assistant/conversations/<int:conversation_id>/messages', methods=['POST'])
def send_message(conversation_id: int):
    """
    发送用户消息并获取 AI 回复

    Request Body:
        content: 消息内容 (必填)
        page_context: 当前页面上下文 (可选)

    Returns:
        200: 用户消息和 AI 回复
    """
    auth_error = require_login()
    if auth_error:
        return auth_error

    user_id = g.user['id']
    data = request.get_json() or {}

    content = data.get('content', '').strip()
    if not content:
        return make_error_response('INVALID_REQUEST', '消息内容不能为空', 400)

    if len(content) > 2000:
        return make_error_response('INVALID_REQUEST', '消息内容过长（最多 2000 字符）', 400)

    page_context = data.get('page_context')

    try:
        service = get_conversation_service()

        # 验证会话权限
        conversation = service.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return make_error_response('NOT_FOUND', '会话不存在或无权访问', 404)

        # 保存用户消息
        user_message = service.add_message(
            conversation_id=conversation_id,
            role='user',
            content=content,
            trigger_type='user_message',
            metadata={'page_context': page_context} if page_context else None
        )

        # 调用 AI 生成回复
        try:
            from services.ai_content_service import call_ai_for_conversation

            # 获取最近消息作为上下文
            recent_messages = service.get_recent_messages(conversation_id, limit=10)

            # 调用 AI
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                ai_response = loop.run_until_complete(
                    call_ai_for_conversation(
                        user_info=g.user,
                        messages=recent_messages,
                        page_context=page_context
                    )
                )
            finally:
                loop.close()

            # 保存 AI 回复
            assistant_message = service.add_message(
                conversation_id=conversation_id,
                role='assistant',
                content=ai_response,
                trigger_type='user_message',
                metadata={'page_context': page_context} if page_context else None
            )

            # 强制执行消息限制
            service.enforce_message_limit(conversation_id, max_messages=100)

        except Exception as ai_error:
            logger.error(f"AI 调用失败: {ai_error}")
            # AI 不可用时的回退消息
            assistant_message = service.add_message(
                conversation_id=conversation_id,
                role='assistant',
                content='抱歉，AI 服务暂时不可用，请稍后再试。如有紧急问题，请联系管理员。',
                trigger_type='user_message',
                metadata={'error': str(ai_error)}
            )

        return jsonify({
            'status': 'success',
            'data': {
                'user_message': user_message.to_dict(),
                'assistant_message': assistant_message.to_dict()
            }
        })

    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return make_error_response('INTERNAL_ERROR', f'发送消息失败: {str(e)}', 500)


@bp.route('/api/assistant/conversations/<int:conversation_id>/archive', methods=['POST'])
def archive_conversation(conversation_id: int):
    """
    归档会话

    Returns:
        200: 归档成功
    """
    auth_error = require_login()
    if auth_error:
        return auth_error

    user_id = g.user['id']

    try:
        service = get_conversation_service()
        success = service.archive_conversation(conversation_id, user_id)

        if not success:
            return make_error_response('NOT_FOUND', '会话不存在或无权访问', 404)

        return jsonify({
            'status': 'success',
            'message': '会话已归档'
        })

    except Exception as e:
        logger.error(f"归档会话失败: {e}")
        return make_error_response('INTERNAL_ERROR', f'归档会话失败: {str(e)}', 500)


# ==================== 触发端点 ====================

@bp.route('/api/assistant/trigger/page-change', methods=['POST'])
def trigger_page_change():
    """
    页面切换时触发 AI 主动问候（受速率限制）

    Request Body:
        page_context: 页面上下文 (必填)
        page_url: 页面 URL (可选，用于日志)

    Returns:
        200: 触发结果
    """
    auth_error = require_login()
    if auth_error:
        return auth_error

    user_id = g.user['id']
    data = request.get_json() or {}

    page_context = data.get('page_context')
    if not page_context:
        return make_error_response('INVALID_REQUEST', '缺少 page_context 参数', 400)

    try:
        service = get_conversation_service()

        # 检查速率限制
        allowed, remaining = service.check_rate_limit(user_id, cooldown_seconds=60)

        if not allowed:
            return jsonify({
                'status': 'success',
                'data': {
                    'triggered': False,
                    'reason': 'rate_limited',
                    'retry_after': remaining
                }
            })

        # 更新速率限制
        service.update_rate_limit(user_id)

        # 获取或创建活跃对话
        conversation = service.get_active_conversation(user_id)

        # 生成页面问候语
        try:
            from services.ai_content_service import generate_page_greeting

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                greeting = loop.run_until_complete(
                    generate_page_greeting(
                        user_info=g.user,
                        page_context=page_context
                    )
                )
            finally:
                loop.close()

            # 保存问候消息
            message = service.add_message(
                conversation_id=conversation.id,
                role='assistant',
                content=greeting,
                trigger_type='page_change',
                metadata={'page_context': page_context}
            )

            return jsonify({
                'status': 'success',
                'data': {
                    'triggered': True,
                    'message': message.to_dict()
                }
            })

        except Exception as ai_error:
            logger.error(f"生成页面问候失败: {ai_error}")
            return jsonify({
                'status': 'success',
                'data': {
                    'triggered': False,
                    'reason': 'ai_unavailable'
                }
            })

    except Exception as e:
        logger.error(f"页面切换触发失败: {e}")
        return make_error_response('INTERNAL_ERROR', f'触发失败: {str(e)}', 500)


@bp.route('/api/assistant/trigger/operation', methods=['POST'])
def trigger_operation():
    """
    操作完成时触发 AI 反馈（受速率限制）

    Request Body:
        operation_type: 操作类型 (必填)
        operation_result: 操作结果 success/error (必填)
        operation_details: 操作详情 (可选)

    Returns:
        200: 触发结果
    """
    auth_error = require_login()
    if auth_error:
        return auth_error

    user_id = g.user['id']
    data = request.get_json() or {}

    operation_type = data.get('operation_type')
    operation_result = data.get('operation_result')
    operation_details = data.get('operation_details', {})

    if not operation_type or not operation_result:
        return make_error_response('INVALID_REQUEST', '缺少必要参数', 400)

    # 验证操作类型
    valid_types = ['generate_grader', 'parse_document', 'export_grades', 'import_students', 'create_class']
    if operation_type not in valid_types:
        return make_error_response('INVALID_REQUEST', f'无效的操作类型: {operation_type}', 400)

    try:
        service = get_conversation_service()

        # 检查速率限制
        allowed, remaining = service.check_rate_limit(user_id, cooldown_seconds=60)

        if not allowed:
            return jsonify({
                'status': 'success',
                'data': {
                    'triggered': False,
                    'reason': 'rate_limited',
                    'retry_after': remaining
                }
            })

        # 更新速率限制
        service.update_rate_limit(user_id)

        # 获取或创建活跃对话
        conversation = service.get_active_conversation(user_id)

        # 生成操作反馈
        try:
            from services.ai_content_service import generate_operation_feedback

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                feedback = loop.run_until_complete(
                    generate_operation_feedback(
                        user_info=g.user,
                        operation_type=operation_type,
                        operation_result=operation_result,
                        details=operation_details
                    )
                )
            finally:
                loop.close()

            # 保存反馈消息
            message = service.add_message(
                conversation_id=conversation.id,
                role='assistant',
                content=feedback,
                trigger_type='operation_complete',
                metadata={
                    'operation_type': operation_type,
                    'operation_result': operation_result,
                    'details': operation_details
                }
            )

            return jsonify({
                'status': 'success',
                'data': {
                    'triggered': True,
                    'message': message.to_dict()
                }
            })

        except Exception as ai_error:
            logger.error(f"生成操作反馈失败: {ai_error}")
            return jsonify({
                'status': 'success',
                'data': {
                    'triggered': False,
                    'reason': 'ai_unavailable'
                }
            })

    except Exception as e:
        logger.error(f"操作触发失败: {e}")
        return make_error_response('INTERNAL_ERROR', f'触发失败: {str(e)}', 500)


# ==================== 轮询端点 ====================

@bp.route('/api/assistant/poll', methods=['GET'])
def poll_messages():
    """
    轮询新消息（用于多标签页同步）

    Query Params:
        conversation_id: 当前会话 ID (必填)
        last_message_id: 已知的最后消息 ID (必填)

    Returns:
        200: 新消息列表
    """
    auth_error = require_login()
    if auth_error:
        return auth_error

    user_id = g.user['id']

    try:
        conversation_id = int(request.args.get('conversation_id', 0))
        last_message_id = int(request.args.get('last_message_id', 0))
    except (ValueError, TypeError):
        return make_error_response('INVALID_REQUEST', '参数无效', 400)

    if not conversation_id or last_message_id < 0:
        return make_error_response('INVALID_REQUEST', '缺少必要参数', 400)

    try:
        service = get_conversation_service()

        # 验证会话权限
        conversation = service.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return make_error_response('NOT_FOUND', '会话不存在或无权访问', 404)

        # 获取新消息
        new_messages = service.get_messages_after(conversation_id, last_message_id)

        return jsonify({
            'status': 'success',
            'data': {
                'has_new': len(new_messages) > 0,
                'messages': [msg.to_dict() for msg in new_messages]
            }
        })

    except Exception as e:
        logger.error(f"轮询消息失败: {e}")
        return make_error_response('INTERNAL_ERROR', f'轮询失败: {str(e)}', 500)
