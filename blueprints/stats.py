"""
统计 API 蓝图
提供仪表盘统计数据的 API 接口
"""
from flask import Blueprint, jsonify, session, g

bp = Blueprint('stats', __name__, url_prefix='/api/stats')


@bp.route('/summary', methods=['GET'])
def get_summary():
    """
    获取仪表盘统计数据汇总
    Response: {
        'class_count': int,
        'student_count': int,
        'grader_count': int,
        'pending_task_count': int,
        'recent_classes': [...],
        'recent_graders': [...]
    }
    """
    if not g.user:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401

    from services.stats_service import StatsService

    user_id = g.user['id']
    stats_service = StatsService(session)

    data = stats_service.get_all_data(user_id)

    return jsonify(data)


@bp.route('/refresh', methods=['POST'])
def refresh():
    """
    手动刷新统计数据缓存
    Response: {
        'status': 'success',
        'data': { ... }
    }
    """
    if not g.user:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401

    from services.stats_service import StatsService

    user_id = g.user['id']
    stats_service = StatsService(session)

    data = stats_service.refresh_cache(user_id)

    return jsonify({
        'status': 'success',
        'data': data
    })
