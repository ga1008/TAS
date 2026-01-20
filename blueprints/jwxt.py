"""
教务系统同步蓝图
支持两种登录信息存储方式：
1. 持久保存（数据库）：用户选择"记住登录"时使用
2. 临时会话（Session）：用户选择"不保存"时使用，会话结束即失效
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
    source: 'session' | 'database' | None
    """
    # 1. 优先检查 Session 中的临时凭证
    temp_creds = session.get(JWXT_SESSION_KEY)
    if temp_creds and temp_creds.get('username') and temp_creds.get('password'):
        return temp_creds, 'session'

    # 2. 检查数据库中的激活绑定
    binding = db.get_jwxt_binding(user_id, only_active=True)
    if binding:
        return {
            'username': binding['jwxt_username'],
            'password': binding['jwxt_password'],
            'last_check': binding.get('last_check_at')
        }, 'database'

    # 3. 检查数据库中是否有失效的绑定（用于提示用户）
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
        del session[JWXT_SESSION_KEY]


def save_session_credentials(username, password, teacher_info=None):
    """保存临时凭证到 Session"""
    session[JWXT_SESSION_KEY] = {
        'username': username,
        'password': password,
        'teacher_info': teacher_info or {}
    }


def get_auto_logged_client(user_id):
    """
    [Core] 获取已自动登录的 JWXT 客户端
    供其他模块调用，如果登录失败会标记绑定为失效
    """
    credentials, source = get_effective_credentials(user_id)

    if not credentials or credentials.get('is_expired'):
        raise Exception("未绑定教务系统账号或凭证已失效")

    # 初始化客户端并登录
    client = JwxtClient()
    success, msg = client.login(credentials['username'], credentials['password'])

    if not success:
        # 登录失败，根据来源处理
        if source == 'database':
            # 数据库凭证失效，更新状态
            db.update_jwxt_binding_status(user_id, False)
        elif source == 'session':
            # Session 凭证失效，清除
            clear_session_credentials()

        raise Exception(f"自动登录失败: {msg}")

    # 登录成功，更新最后检查时间
    if source == 'database':
        db.update_jwxt_last_check(user_id)

    return client


@bp.route('/view', methods=['GET'])
def page_connect():
    """教务系统连接页面"""
    return render_template('jwxt_connect.html', user=g.user)


# 保留旧路由作为兼容
@bp.route('/test', methods=['GET'])
def page_connect_legacy():
    return render_template('jwxt_connect.html', user=g.user)


@bp.route('/status', methods=['GET'])
def check_status():
    """
    检查当前用户的连接状态（增强版）
    返回详细的状态信息，包括凭证来源和有效性
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({
            "code": 401,
            "msg": "未登录系统",
            "status": "not_logged_in",
            "linked": False
        })

    credentials, source = get_effective_credentials(user_id)

    if not credentials:
        return jsonify({
            "code": 200,
            "status": "not_linked",
            "linked": False
        })

    if credentials.get('is_expired'):
        return jsonify({
            "code": 200,
            "status": "expired",
            "linked": False,
            "username": credentials.get('username'),
            "message": "登录凭证已失效，请重新登录"
        })

    # 有有效凭证
    response_data = {
        "code": 200,
        "status": "active",
        "linked": True,
        "username": credentials.get('username'),
        "source": source,  # 'session' 或 'database'
        "persistent": source == 'database',  # 是否持久保存
        "last_check": credentials.get('last_check', '未知')
    }

    # 如果是 Session 存储，添加教师信息
    if source == 'session' and credentials.get('teacher_info'):
        response_data['teacher_info'] = credentials['teacher_info']

    return jsonify(response_data)


@bp.route('/connect', methods=['POST'])
def connect_jwxt():
    """
    连接教务系统
    根据 remember 参数决定存储方式
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)  # 默认不记住（临时会话）
    user_id = session.get('user_id')

    if not username or not password:
        return jsonify({"code": 400, "msg": "请输入账号密码"}), 400

    # 1. 初始化客户端并登录验证
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

    # 3. 根据用户选择存储凭证
    if remember and user_id:
        # 持久保存到数据库
        try:
            db.save_jwxt_binding(user_id, username, password)
            # 清除可能存在的 Session 临时凭证
            clear_session_credentials()
        except Exception as e:
            print(f"[DB Error] Save binding failed: {e}")
            return jsonify({"code": 500, "msg": "保存失败，请重试"}), 500
    else:
        # 临时保存到 Session
        save_session_credentials(username, password, teacher_info)

    return jsonify({
        "code": 200,
        "msg": "连接成功",
        "persistent": remember,
        "data": teacher_info
    })


@bp.route('/update', methods=['POST'])
def update_jwxt():
    """
    更新教务系统绑定信息
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', True)  # 更新时默认记住
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"code": 401, "msg": "未登录系统"}), 401

    if not username or not password:
        return jsonify({"code": 400, "msg": "请输入账号密码"}), 400

    # 1. 先测试登录
    client = JwxtClient()
    success, msg = client.login(username, password)

    if not success:
        return jsonify({"code": 401, "msg": f"登录验证失败: {msg}"}), 401

    # 2. 获取教师信息
    teacher_info = {}
    info, err = client.get_teacher_info()
    if not err and info:
        teacher_info = {
            "name": info.get('name'),
            "college": info.get('college'),
            "role": info.get('role')
        }

    # 3. 根据用户选择存储
    if remember:
        try:
            db.save_jwxt_binding(user_id, username, password)
            clear_session_credentials()
        except Exception as e:
            print(f"[DB Error] Update binding failed: {e}")
            return jsonify({"code": 500, "msg": "保存失败，请重试"}), 500
    else:
        save_session_credentials(username, password, teacher_info)
        # 如果之前有数据库绑定，删除它
        db.delete_jwxt_binding(user_id)

    return jsonify({
        "code": 200,
        "msg": "更新成功",
        "persistent": remember,
        "data": teacher_info
    })


@bp.route('/test_login', methods=['POST'])
def test_login():
    """仅测试登录，不保存"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"code": 400, "msg": "请输入账号密码"}), 400

    client = JwxtClient()
    success, msg = client.login(username, password)

    if not success:
        return jsonify({"code": 401, "msg": msg, "success": False}), 401

    # 获取用户信息
    info, err = client.get_teacher_info()
    if err:
        return jsonify({
            "code": 200,
            "msg": "登录成功，但获取信息失败",
            "success": True,
            "data": {}
        })

    return jsonify({
        "code": 200,
        "msg": "登录成功",
        "success": True,
        "data": {
            "name": info.get('name'),
            "college": info.get('college'),
            "role": info.get('role')
        }
    })


@bp.route('/disconnect', methods=['POST'])
def disconnect_jwxt():
    """解除绑定（同时清除数据库和 Session）"""
    user_id = session.get('user_id')

    # 清除 Session 临时凭证
    clear_session_credentials()

    # 清除数据库绑定
    if user_id:
        db.delete_jwxt_binding(user_id)

    return jsonify({"code": 200, "msg": "已解除绑定"})


@bp.route('/info', methods=['GET'])
def get_user_info():
    """
    获取当前绑定账号的详细信息
    需要重新登录验证以获取最新信息
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"code": 401, "msg": "未登录系统"}), 401

    credentials, source = get_effective_credentials(user_id)

    if not credentials or credentials.get('is_expired'):
        return jsonify({
            "code": 404,
            "msg": "未绑定教务系统或凭证已失效",
            "need_reauth": True
        }), 404

    # 尝试登录获取信息
    client = JwxtClient()
    success, msg = client.login(credentials['username'], credentials['password'])

    if not success:
        # 登录失败，标记为失效
        if source == 'database':
            db.update_jwxt_binding_status(user_id, False)
        elif source == 'session':
            clear_session_credentials()

        return jsonify({
            "code": 401,
            "msg": "绑定的账号登录失败，可能密码已变更",
            "need_reauth": True
        }), 401

    # 登录成功，更新最后检查时间
    if source == 'database':
        db.update_jwxt_last_check(user_id)

    # 获取用户信息
    info, err = client.get_teacher_info()
    if err:
        return jsonify({"code": 500, "msg": f"获取信息失败: {err}"}), 500

    return jsonify({
        "code": 200,
        "data": {
            "username": credentials['username'],
            "name": info.get('name'),
            "college": info.get('college'),
            "role": info.get('role'),
            "source": source,
            "persistent": source == 'database',
            "last_check": credentials.get('last_check')
        }
    })


@bp.route('/verify', methods=['POST'])
def verify_credentials():
    """
    验证当前凭证是否仍然有效
    用于前端检查凭证状态
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"valid": False, "reason": "not_logged_in"})

    credentials, source = get_effective_credentials(user_id)

    if not credentials or credentials.get('is_expired'):
        return jsonify({"valid": False, "reason": "no_credentials"})

    # 尝试登录验证
    client = JwxtClient()
    success, msg = client.login(credentials['username'], credentials['password'])

    if not success:
        # 登录失败，标记为失效
        if source == 'database':
            db.update_jwxt_binding_status(user_id, False)
        elif source == 'session':
            clear_session_credentials()

        return jsonify({
            "valid": False,
            "reason": "login_failed",
            "message": msg
        })

    # 更新最后检查时间
    if source == 'database':
        db.update_jwxt_last_check(user_id)

    return jsonify({
        "valid": True,
        "source": source,
        "persistent": source == 'database'
    })
