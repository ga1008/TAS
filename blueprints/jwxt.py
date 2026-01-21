"""
blueprints/jwxt.py
教务系统同步蓝图
改进说明：
1. 严格区分持久化(DB)和临时(Session)存储，确保二者互斥。
2. 增加登录失效后的自动状态更新，配合前端实现自动弹窗。
"""
from flask import Blueprint, request, jsonify, render_template, session, g

from extensions import db
from services.jwxt.client import JwxtClient

bp = Blueprint('jwxt', __name__, url_prefix='/jwxt')

# Session 中存储临时登录信息的 key
JWXT_SESSION_KEY = 'jwxt_temp_credentials'


def get_effective_credentials(user_id):
    """
    获取当前有效的教务系统登录凭证
    优先级：Session临时凭证 > 数据库激活凭证
    返回: (credentials_dict, source) 或 (None, None)
    source: 'session' | 'database' | 'expired'
    """
    # 1. 优先检查 Session 中的临时凭证 (用于未勾选"记住我"的场景)
    temp_creds = session.get(JWXT_SESSION_KEY)
    if temp_creds and temp_creds.get('username') and temp_creds.get('password'):
        return temp_creds, 'session'

    # 2. 检查数据库中的激活绑定 (用于勾选"记住我"的场景)
    binding = db.get_jwxt_binding(user_id, only_active=True)
    if binding:
        return {
            'username': binding['jwxt_username'],
            'password': binding['jwxt_password'],
            'last_check': binding.get('last_check_at')
        }, 'database'

    # 3. 检查数据库中是否有失效的绑定 (用于UI显示"已过期"并触发自动弹窗)
    inactive_binding = db.get_jwxt_binding(user_id, only_active=False)
    if inactive_binding and not inactive_binding.get('is_active'):
        return {
            'username': inactive_binding['jwxt_username'],
            'is_expired': True
        }, 'expired'

    return None, None


def clear_session_credentials():
    """清除 Session 中的临时凭证"""
    if JWXT_SESSION_KEY in session:
        session.pop(JWXT_SESSION_KEY, None)


def save_session_credentials(username, password, teacher_info=None):
    """保存临时凭证到 Session"""
    session[JWXT_SESSION_KEY] = {
        'username': username,
        'password': password,
        'teacher_info': teacher_info or {}
    }


@bp.route('/view', methods=['GET'])
def page_connect():
    """教务系统连接页面"""
    return render_template('jwxt_connect.html', user=g.user)


@bp.route('/status', methods=['GET'])
def check_status():
    """
    检查当前用户的连接状态 (Phase 1)
    前端页面加载时调用，用于快速判断显示状态，不进行耗时的登录验证。
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"code": 401, "msg": "未登录系统", "linked": False})

    credentials, source = get_effective_credentials(user_id)

    if not credentials:
        return jsonify({"code": 200, "status": "not_linked", "linked": False})

    # 如果是已过期的数据库绑定
    if source == 'expired' or credentials.get('is_expired'):
        return jsonify({
            "code": 200,
            "status": "expired",
            "linked": False,
            "username": credentials.get('username'),
            "message": "登录凭证已失效，请重新登录"
        })

    # 看起来是连接状态 (Session或DB有值)
    response_data = {
        "code": 200,
        "status": "active",
        "linked": True,
        "username": credentials.get('username'),
        "source": source,
        "persistent": source == 'database',
        "last_check": credentials.get('last_check', '刚刚')
    }

    # 如果是 Session 存储，直接返回缓存的教师信息，前端可预渲染
    if source == 'session' and credentials.get('teacher_info'):
        response_data['teacher_info'] = credentials['teacher_info']

    return jsonify(response_data)


@bp.route('/connect', methods=['POST'])
def connect_jwxt():
    """
    连接/登录教务系统
    逻辑：先验证登录，成功后根据 remember 参数严格决定存储位置（互斥）。
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)  # true=存数据库, false=存Session
    user_id = session.get('user_id')

    if not username or not password:
        return jsonify({"code": 400, "msg": "请输入账号密码"}), 400

    # 1. 实际登录验证
    client = JwxtClient()
    success, msg = client.login(username, password)

    if not success:
        return jsonify({"code": 401, "msg": msg}), 401

    # 2. 获取教师信息
    teacher_info = {}
    info, err = client.get_teacher_info()
    if not err and info:
        teacher_info = {
            "name": info.get('name'),
            "college": info.get('college'),
            "role": info.get('role')
        }

    # 3. 存储凭证 (互斥逻辑)
    if remember and user_id:
        # 模式 A: 持久保存 -> 存DB，同时必须清除Session，防止混淆
        try:
            db.save_jwxt_binding(user_id, username, password)
            clear_session_credentials()
        except Exception as e:
            return jsonify({"code": 500, "msg": "保存到数据库失败"}), 500
    else:
        # 模式 B: 临时会话 -> 存Session，同时必须删除DB中的旧绑定
        # 满足需求1：不勾选记住按钮，信息保留直到Session过期
        save_session_credentials(username, password, teacher_info)
        if user_id:
            db.delete_jwxt_binding(user_id)

    return jsonify({
        "code": 200,
        "msg": "连接成功",
        "persistent": remember,
        "data": teacher_info
    })


@bp.route('/update', methods=['POST'])
def update_jwxt():
    """更新绑定信息 (逻辑同 connect，复用前端接口)"""
    return connect_jwxt()


@bp.route('/info', methods=['GET'])
def get_user_info():
    """
    获取详细信息与实时验证 (Phase 2)
    前端在 check_status 返回 linked=True 后调用。

    关键逻辑：
    满足需求2：如果自动连接检查失败（如密码已改），返回 401 和用户名，
    触发前端自动弹窗。
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"code": 401, "msg": "未登录系统"}), 401

    credentials, source = get_effective_credentials(user_id)

    if not credentials or credentials.get('is_expired'):
        return jsonify({
            "code": 404,
            "msg": "无有效凭证",
            "need_reauth": True
        }), 404

    # 尝试使用存储的凭证登录
    client = JwxtClient()
    success, msg = client.login(credentials['username'], credentials['password'])

    if not success:
        # 登录失败处理
        if source == 'database':
            # 标记数据库记录为失效，下次 /status 检查会直接返回 expired
            db.update_jwxt_binding_status(user_id, False)
        elif source == 'session':
            # Session 凭证失效，直接清除
            clear_session_credentials()

        # 返回 401 状态码，且携带 username，方便前端弹出模态框预填
        return jsonify({
            "code": 401,
            "msg": f"教务系统登录失败: {msg}",
            "need_reauth": True,
            "username": credentials['username']
        }), 401

    # 登录成功，更新最后检查时间 (仅DB模式)
    if source == 'database':
        db.update_jwxt_last_check(user_id)

    # 获取用户信息
    info, err = client.get_teacher_info()

    return jsonify({
        "code": 200,
        "data": {
            "username": credentials['username'],
            "name": info.get('name') if info else "获取失败",
            "college": info.get('college') if info else "",
            "role": info.get('role') if info else "教师",
            "source": source,
            "persistent": source == 'database',
            "last_check": credentials.get('last_check')
        }
    })


@bp.route('/disconnect', methods=['POST'])
def disconnect_jwxt():
    """断开连接"""
    user_id = session.get('user_id')
    clear_session_credentials()
    if user_id:
        db.delete_jwxt_binding(user_id)
    return jsonify({"code": 200, "msg": "已断开连接"})


@bp.route('/test_login', methods=['POST'])
def test_login():
    """仅测试账号密码，不保存"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"code": 400, "msg": "请输入账号密码"}), 400

    client = JwxtClient()
    success, msg = client.login(username, password)

    if not success:
        return jsonify({"code": 401, "msg": msg, "success": False}), 401

    info, _ = client.get_teacher_info()
    return jsonify({
        "code": 200,
        "msg": "验证通过",
        "success": True,
        "data": info
    })