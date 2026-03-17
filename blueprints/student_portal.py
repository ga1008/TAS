import uuid
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

student_portal_bp = Blueprint('student_portal', __name__, url_prefix='/student')

# 内存字典用于存储当前有效的单设备会话 (生产环境中建议转入 Redis 或 TAS 原有的 Database 实例中)
ACTIVE_STUDENT_SESSIONS = {}
from extensions import db


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


@student_portal_bp.before_app_request
def enforce_single_device():
    # 仅管控进入 /student (除 /login) 的路由
    if request.path.startswith('/student') and not request.path.endswith('/login'):
        student_id = session.get('student_id')
        client_session_id = session.get('device_session_id')

        if not student_id or not client_session_id:
            return redirect(url_for('student_portal.login'))

        # 3. 如果当前设备携带的 session_id 与全局记录不匹配，说明被新登录踢出
        if ACTIVE_STUDENT_SESSIONS.get(student_id) != client_session_id:
            session.clear()
            flash("系统提示：您的账号已在其他设备登录，当前连接已被下线。", "error")
            return redirect(url_for('student_portal.login'))
    return None


@student_portal_bp.route('/dashboard')
def dashboard():
    return render_template('student/dashboard.html')
