from flask import Blueprint, render_template

classroom_bp = Blueprint('classroom', __name__, url_prefix='/classroom')


@classroom_bp.route('/course_manage')
def course_manage():
    # 获取 TAS 班级管理中的前置数据：已导入的班级/学生名单
    # classes = db.get_all_classes()
    return render_template('classroom/course_manage.html', classes=[])


@classroom_bp.route('/files')
def files():
    # 迁移 classshare 资源管理逻辑
    return render_template('classroom/files.html')


@classroom_bp.route('/seminar')
def seminar():
    # 迁移 classshare 在线研讨室视图
    return render_template('classroom/seminar.html')
