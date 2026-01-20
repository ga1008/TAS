"""
通知中心蓝图
提供通知相关的 API 接口和服务函数
"""
from flask import Blueprint, jsonify, request, g

from extensions import db

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


# ================= 通知类型配置 =================

NOTIFICATION_TYPES = {
    'task_pending': {
        'icon': 'hourglass-half',
        'color': 'info',
        'category': 'task'
    },
    'task_processing': {
        'icon': 'cog',
        'color': 'processing',
        'category': 'task'
    },
    'task_success': {
        'icon': 'check-circle',
        'color': 'success',
        'category': 'task'
    },
    'task_failed': {
        'icon': 'exclamation-triangle',
        'color': 'error',
        'category': 'task'
    },
    'system': {
        'icon': 'info-circle',
        'color': 'info',
        'category': 'system'
    }
}


# ================= API 端点 =================

@bp.route('', methods=['GET'])
def get_notifications():
    """
    获取当前用户的通知列表
    Query params:
        - limit: 返回数量限制 (默认 20)
        - include_read: 是否包含已读通知 (默认 false)
    """
    if not g.user:
        return jsonify({'notifications': [], 'unread_count': 0})

    user_id = g.user['id']
    limit = request.args.get('limit', 20, type=int)
    include_read = request.args.get('include_read', 'false').lower() == 'true'

    # 获取通知列表
    notifications = db.get_notifications(user_id, limit=limit, include_read=include_read)

    # 格式化通知数据
    formatted_notifications = []
    for notif in notifications:
        notif_type = notif.get('type', 'system')
        type_config = NOTIFICATION_TYPES.get(notif_type, NOTIFICATION_TYPES['system'])

        formatted_notifications.append({
            'id': notif['id'],
            'type': notif_type,
            'icon': type_config['icon'],
            'color': type_config['color'],
            'category': type_config['category'],
            'title': notif['title'],
            'message': notif['message'],
            'detail': notif['detail'],
            'link': notif['link'],
            'is_read': bool(notif['is_read']),
            'time': notif['created_at'],
            'related_id': notif['related_id']
        })

    # 获取未读数量
    unread_count = db.get_unread_notification_count(user_id)

    return jsonify({
        'notifications': formatted_notifications,
        'unread_count': unread_count
    })


@bp.route('/count', methods=['GET'])
def get_unread_count():
    """获取未读通知数量"""
    if not g.user:
        return jsonify({'unread_count': 0})

    count = db.get_unread_notification_count(g.user['id'])
    return jsonify({'unread_count': count})


@bp.route('/read/<int:notification_id>', methods=['POST'])
def mark_as_read(notification_id):
    """标记单条通知为已读"""
    if not g.user:
        return jsonify({'success': False, 'message': '未登录'}), 401

    db.mark_notification_read(notification_id, g.user['id'])
    return jsonify({'success': True})


@bp.route('/read-all', methods=['POST'])
def mark_all_as_read():
    """标记所有通知为已读"""
    if not g.user:
        return jsonify({'success': False, 'message': '未登录'}), 401

    db.mark_all_notifications_read(g.user['id'])
    return jsonify({'success': True})


@bp.route('/delete/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """删除单条通知"""
    if not g.user:
        return jsonify({'success': False, 'message': '未登录'}), 401

    db.delete_notification(notification_id, g.user['id'])
    return jsonify({'success': True})


# ================= 服务函数（供其他模块调用）=================

class NotificationService:
    """通知服务类，提供通知创建和管理的便捷方法"""

    @staticmethod
    def notify_task_created(user_id, task_id, task_name):
        """任务创建时发送通知"""
        return db.create_task_notification(
            user_id=user_id,
            task_id=task_id,
            task_name=task_name,
            status='pending',
            log_info='任务已提交，等待处理...'
        )

    @staticmethod
    def notify_task_processing(user_id, task_id, task_name, log_info=None):
        """任务开始处理时更新通知"""
        related_id = f"task_{task_id}"

        # 更新现有通知或创建新通知
        db.update_notification_by_related_id(
            related_id=related_id,
            notif_type='task_processing',
            title='正在生成批改核心',
            detail=log_info[:100] + '...' if log_info and len(log_info) > 100 else log_info
        )

    @staticmethod
    def notify_task_success(user_id, task_id, task_name, grader_id):
        """任务成功完成时更新通知"""
        related_id = f"task_{task_id}"
        link = f"/grader/{grader_id}" if grader_id else None

        db.update_notification_by_related_id(
            related_id=related_id,
            notif_type='task_success',
            title='批改核心生成完成',
            detail='点击查看详情',
            link=link
        )

    @staticmethod
    def notify_task_failed(user_id, task_id, task_name, error_message=None):
        """任务失败时更新通知"""
        related_id = f"task_{task_id}"

        detail = error_message[:100] + '...' if error_message and len(error_message) > 100 else error_message
        db.update_notification_by_related_id(
            related_id=related_id,
            notif_type='task_failed',
            title='批改核心生成失败',
            detail=detail
        )

    @staticmethod
    def notify_system(user_id, title, message, link=None):
        """发送系统通知"""
        return db.create_notification(
            user_id=user_id,
            notif_type='system',
            title=title,
            message=message,
            link=link
        )

    @staticmethod
    def cleanup_task_notifications(task_id):
        """清理任务相关的通知（任务删除时调用）"""
        related_id = f"task_{task_id}"
        db.delete_notifications_by_related_id(related_id)
