from flask import Blueprint, request, jsonify, render_template

from services.jwxt.client import JwxtClient

bp = Blueprint('jwxt', __name__, url_prefix='/jwxt')


@bp.route('/test', methods=['GET'])
def page_connect():
    return render_template('jwxt_connect.html')


@bp.route('/connect', methods=['POST'])
def connect_jwxt():
    """
    连接教务系统并获取基础信息
    注意：这里演示的是无状态连接，每次请求新建 Client。
    生产环境可考虑将 Client 序列化或暂存。
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"code": 400, "msg": "请输入账号密码"}), 400

    # 1. 初始化客户端
    client = JwxtClient()

    # 2. 执行登录
    success, msg = client.login(username, password)
    if not success:
        return jsonify({"code": 401, "msg": msg}), 401

    # 3. 立即查询用户信息
    info, err = client.get_teacher_info()
    if err:
        return jsonify({"code": 500, "msg": f"登录成功但查询信息失败: {err}"}), 500

    # 4. 返回结果
    return jsonify({
        "code": 200,
        "msg": "连接成功",
        "data": {
            "name": info.get('name'),
            "college": info.get('college'),
            "role": info.get('role')
        }
    })
