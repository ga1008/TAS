from flask import Blueprint, render_template, g, session

from extensions import db

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """仪表盘首页"""
    from services.stats_service import StatsService

    user_id = g.user['id']
    stats_service = StatsService(session)

    # 获取仪表盘数据
    dashboard_data = stats_service.get_all_data(user_id)

    # 添加页面上下文用于 AI 欢迎语
    dashboard_data['page_context'] = 'dashboard'

    return render_template('dashboard.html', user=g.user, **dashboard_data)


@bp.route('/tasks')
def tasks():
    """批改任务列表页面"""
    classes = db.get_classes(user_id=g.user['id'])

    # 为每个班级添加统计信息
    for cls in classes:
        # 获取班级学生数
        conn = db.get_connection()
        student_count_row = conn.execute(
            'SELECT COUNT(*) as count FROM students WHERE class_id=?',
            (cls['id'],)
        ).fetchone()
        cls['student_count'] = student_count_row['count'] if student_count_row else 0

        # 获取已批改数
        graded_count_row = conn.execute(
            'SELECT COUNT(*) as count FROM grades WHERE class_id=?',
            (cls['id'],)
        ).fetchone()
        cls['graded_count'] = graded_count_row['count'] if graded_count_row else 0

    return render_template('tasks.html', classes=classes, user=g.user)


@bp.route('/intro')
def intro():
    return render_template('intro.html')
