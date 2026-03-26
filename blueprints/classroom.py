from flask import Blueprint, render_template, request, jsonify, g

from extensions import db
from services.file_service import FileService

classroom_bp = Blueprint('classroom', __name__, url_prefix='/classroom')


@classroom_bp.route('/course_manage')
def course_manage():
    # 教师权限页面：只允许已登录用户访问
    if not g.user:
        return render_template('auth/login.html')

    # 获取当前教师创建的 classes 供管理
    classes = db.get_classes(user_id=g.user['id'])
    return render_template('classroom/course_manage.html', classes=classes, user=g.user)


@classroom_bp.route('/files')
def files():
    if not g.user:
        return render_template('auth/login.html')
    # 迁移 classshare 资源管理逻辑
    return render_template('classroom/files.html', user=g.user)


@classroom_bp.route('/seminar')
def seminar():
    if not g.user:
        return render_template('auth/login.html')
    # 迁移 classshare 在线研讨室视图
    return render_template('classroom/seminar.html', user=g.user)


@classroom_bp.route('/api/create_course', methods=['POST'])
def api_create_course():
    """教师端：创建课程条目（轻量），不会自动绑定班级"""
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.json or {}
    name = data.get('name')
    course = data.get('course') or ''
    strategy = data.get('strategy') or 'server_config_2025'
    semester = data.get('semester') or ''
    hours = int(data.get('hours') or 0)
    credits = float(data.get('credits') or 0.0)
    description = data.get('description') or ''
    textbook_ids = data.get('textbook_ids') or []

    if not name:
        return jsonify({"msg": "课程名称不能为空"}), 400

    try:
        class_id = db.create_class(name=name, course=course, strategy=strategy, user_id=g.user['id'])
        # update additional fields
        db.update_class_details(class_id, semester=semester, hours=hours, credits=credits, description=description)

        # ensure workspace created
        ws = FileService.get_real_workspace_path(class_id)

        # link textbooks
        for tid in textbook_ids:
            try:
                db.add_class_textbook(class_id, int(tid))
            except Exception:
                continue

        # 教材目录由教材库维护，课堂记录只保存教材关联

        return jsonify({"status": "success", "class_id": class_id})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@classroom_bp.route('/api/open_class_from_list', methods=['POST'])
def api_open_class_from_list():
    """教师端：使用已导入的学生名单（student_lists.id）创建课堂（classes 表）并将学生写入 students 表。
    请求 body: { "student_list_id": int, "class_name": str, "course": str }
    """
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.json or {}
    student_list_id = data.get('student_list_id')
    class_name = data.get('class_name')
    course = data.get('course', '')

    if not student_list_id or not class_name:
        return jsonify({"msg": "缺少必要信息"}), 400

    try:
        # 1. create class record
        class_id = db.create_class(name=class_name, course=course, strategy='server_config_2025', user_id=g.user['id'])

        # 2. copy students from student_details into students table
        students = db.get_student_details(student_list_id)
        for s in students:
            try:
                db.add_student(student_id=s['student_id'], name=s['name'], class_id=class_id)
            except Exception:
                # ignore duplicates
                continue

        # 3. ensure workspace exists
        ws = FileService.get_real_workspace_path(class_id)

        return jsonify({"status": "success", "class_id": class_id})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@classroom_bp.route('/api/list_classes')
def api_list_classes():
    """返回当前用户可管理的 classes（供前端刷新用）"""
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401
    classes = db.get_classes(user_id=g.user['id'])
    return jsonify({"status": "success", "data": classes})


@classroom_bp.route('/api/get_textbooks')
def api_get_textbooks():
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401
    tbs = db.get_textbooks()
    return jsonify({"status": "success", "data": tbs})


@classroom_bp.route('/api/create_textbook', methods=['POST'])
def api_create_textbook():
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401
    data = request.json or {}
    title = data.get('title')
    if not title:
        return jsonify({"status": "error", "msg": "书名不能为空"}), 400
    try:
        tid = db.create_textbook(title=title, author=data.get('author'), publisher=data.get('publisher'), isbn=data.get('isbn'))
        return jsonify({"status": "success", "id": tid})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@classroom_bp.route('/api/get_class/<int:class_id>')
def api_get_class(class_id):
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401
    cls = db.get_class_with_textbooks(class_id)
    if not cls:
        return jsonify({"status": "error", "msg": "Not found"}), 404
    return jsonify({"status": "success", "data": cls})


@classroom_bp.route('/api/update_course/<int:class_id>', methods=['POST'])
def api_update_course(class_id):
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401
    data = request.json or {}
    # Only allow owner or admin
    cls_record = db.get_class_by_id(class_id)
    if not cls_record:
        return jsonify({"status": "error", "msg": "class not found"}), 404
    is_admin = g.user.get('is_admin')
    is_owner = int(cls_record['created_by']) == int(g.user['id'])
    if not (is_admin or is_owner):
        return jsonify({"status": "error", "msg": "Forbidden"}), 403

    semester = data.get('semester')
    name = data.get('name')
    hours = int(data.get('hours') or 0)
    credits = float(data.get('credits') or 0.0)
    description = data.get('description')
    textbook_ids = data.get('textbook_ids') or []

    try:
        db.update_class_details(class_id, semester=semester, hours=hours, credits=credits, description=description)
        # update name if provided
        if name:
            conn = db.get_connection()
            conn.execute('UPDATE classes SET name=? WHERE id=?', (name, class_id))
            conn.commit()

        # update textbook links: clear then add
        db.delete_class_textbooks(class_id)
        for tid in textbook_ids:
            try:
                db.add_class_textbook(class_id, int(tid))
            except Exception:
                continue

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@classroom_bp.route('/api/delete_course/<int:class_id>', methods=['POST', 'DELETE'])
def api_delete_course(class_id):
    """教师端：删除课程，同时清除级联的课堂学生和成绩记录"""
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    cls_record = db.get_class_by_id(class_id)
    if not cls_record:
        return jsonify({"status": "error", "msg": "课程不存在"}), 404

    # 鉴权：只能由创建者或超级管理员删除
    is_admin = g.user.get('is_admin')
    is_owner = int(cls_record['created_by']) == int(g.user['id'])
    if not (is_admin or is_owner):
        return jsonify({"status": "error", "msg": "权限不足，无法删除此课程"}), 403

    try:
        db.delete_class(class_id)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
