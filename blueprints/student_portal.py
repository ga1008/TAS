import uuid
import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, g, jsonify, current_app, send_file

student_portal_bp = Blueprint('student_portal', __name__, url_prefix='/student')

# 内存字典用于存储当前有效的单设备会话 (生产环境中建议转入 Redis 或 TAS 原有的 Database 实例中)
ACTIVE_STUDENT_SESSIONS = {}
from extensions import db
from services.file_service import FileService


@student_portal_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')

        # 调用 TAS 原有的数据库方法校验学号与姓名匹配关系
        student = db.login_student(student_id, name)

        if student:
            # 1. 颁发全新专属 Session ID
            new_session_id = str(uuid.uuid4())
            session['student_id'] = student_id
            session['student_name'] = name
            session['device_session_id'] = new_session_id

            # 2. 覆盖全局记录，立刻使旧设备持有的 session_id 失效
            ACTIVE_STUDENT_SESSIONS[student_id] = new_session_id

            return redirect(url_for('student_portal.dashboard'))
        else:
            flash("学号或姓名错误，请重新输入。", "error")

    return render_template('student/login.html')


@student_portal_bp.route('/logout')
def logout():
    student_id = session.get('student_id')
    # 安全登出：只有拿着合法且最新 session_id 的设备才能清理掉全局状态
    if student_id and ACTIVE_STUDENT_SESSIONS.get(student_id) == session.get('device_session_id'):
        ACTIVE_STUDENT_SESSIONS.pop(student_id, None)

    session.clear()
    flash("您已安全退出学习终端。", "success")
    return redirect(url_for('student_portal.login'))


@student_portal_bp.before_request
def enforce_single_device():
    """
    Enforce single-device student sessions.
    NOTE: use blueprint.before_request so this runs only for student_portal routes (not globally for all '/student' paths).
    """
    # Only enforce for routes under this blueprint (Flask ensures this function runs only when a student_portal endpoint is matched)
    # Skip login route itself
    if request.endpoint and request.endpoint.endswith('.login'):
        return None

    # Now perform checks for student pages
    # Only paths under /student (the portal) should reach here, but add a defensive guard
    if not request.path.startswith('/student'):
        return None

    student_id = session.get('student_id')
    client_session_id = session.get('device_session_id')

    if not student_id or not client_session_id:
        return redirect(url_for('student_portal.login'))

    # If current device session id does not match the active one, treat as kicked out
    if ACTIVE_STUDENT_SESSIONS.get(student_id) != client_session_id:
        session.clear()
        flash("系统提示：您的账号已在其他设备登录，当前连接已被下线。", "error")
        return redirect(url_for('student_portal.login'))

    return None


@student_portal_bp.route('/dashboard')
def dashboard():
    # Dashboard shows classes the student belongs to and quick links
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('student_portal.login'))

    # 查找学生对应的班级（一个学号可能在多班同时出现，按最近创建排序）
    conn = db.get_connection()
    rows = conn.execute('SELECT DISTINCT c.* FROM classes c JOIN students s ON c.id = s.class_id WHERE s.student_id = ? ORDER BY c.created_at DESC', (student_id,)).fetchall()
    classes = [dict(r) for r in rows]

    return render_template('student/dashboard.html', classes=classes)


@student_portal_bp.route('/preview_file/<int:class_id>/<student_id>')
def preview_file(class_id, student_id):
    """为学生端提供文件预览接口（只允许已登录学生请求）"""
    # 权限：仅学生本人或管理员可请求
    if session.get('student_id') != student_id and not (g.user and g.user.get('is_admin')):
        return jsonify({"msg": "Unauthorized"}), 401

    path = request.args.get('path')
    if not path:
        return jsonify({"msg": "path missing"}), 400

    # 客户端请求预览，转发到 grading service preview logic if exists; fallback: try to read from class workspace
    ws = FileService.get_real_workspace_path(class_id)
    full_path = os.path.normpath(os.path.join(ws, path.lstrip('/')))

    # 防止越界
    if not full_path.startswith(ws):
        return jsonify({"msg": "Invalid path"}), 400

    if not os.path.exists(full_path):
        return jsonify({"msg": "Not found"}), 404

    # 图片 handling
    import mimetypes
    ctype, _ = mimetypes.guess_type(full_path)
    if ctype and ctype.startswith('image'):
        try:
            return send_file(full_path, mimetype=ctype)
        except Exception:
            # fallback to JSON error
            return jsonify({"type": "error", "msg": "Cannot send file"}), 500

    # 否则尝试读取文本
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return jsonify({"type": "text", "content": content})
    except Exception as e:
        return jsonify({"type": "error", "msg": str(e)})
