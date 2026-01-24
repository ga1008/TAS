import functools

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, g

from extensions import db

# url_prefix 设置为 /admin，所有路由自动加上 /admin
bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(view):
    """装饰器：确保用户是管理员"""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        # 检查 g.user (由 auth 蓝图或 before_request 加载)
        # 或者直接检查 session['user']
        user = session.get('user')
        if not user or not user.get('is_admin'):
            return redirect(url_for('admin.login'))
        return view(**kwargs)

    return wrapped_view


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = db.verify_admin_login(username, password)

        if user:
            # 登录成功，写入 session
            # 注意：如果这和普通用户登录冲突，需要考虑 session key 的设计
            # 这里简单起见，覆盖 'user'
            session['user'] = user
            return redirect(url_for('admin.dashboard'))

        flash('管理员账号或密码错误', 'error')

    # 渲染 templates/admin/login.html
    return render_template('admin/login.html')


@bp.route('/check_status')
def check_admin_status():
    """检查当前用户是否具有管理员权限（API端点）"""
    user = session.get('user')
    is_admin = user and user.get('is_admin', False)
    return jsonify({
        'is_admin': is_admin,
        'username': user.get('username') if user else None
    })


@bp.route('/ajax_login', methods=['POST'])
def ajax_login():
    """AJAX 管理员登录端点（用于弹窗登录）"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'message': '请输入账号和密码'}), 400

    user = db.verify_admin_login(username, password)

    if user:
        # 登录成功，更新 session
        session['user'] = user
        return jsonify({
            'success': True,
            'message': '登录成功',
            'redirect': url_for('admin.dashboard')
        })

    return jsonify({'success': False, 'message': '管理员账号或密码错误'}), 401


@bp.route('/')
@admin_required
def dashboard():
    # 获取数据
    providers = db.get_all_providers()
    for p in providers:
        p['models'] = db.get_models_by_provider(p['id'])

    # 渲染 templates/admin/dashboard.html
    return render_template('admin/dashboard.html', providers=providers, user=g.user)


# --- AI Provider Actions ---

@bp.route('/provider/add', methods=['POST'])
@admin_required
def add_provider():
    name = request.form.get('name')
    p_type = request.form.get('provider_type')
    api_key = request.form.get('api_key')
    base_url = request.form.get('base_url')

    try:
        db.add_provider(name, p_type, api_key, base_url)
        flash(f'厂商 {name} 添加成功', 'success')
    except Exception as e:
        flash(f'添加失败: {str(e)}', 'error')

    return redirect(url_for('admin.dashboard'))


@bp.route('/provider/edit', methods=['POST'])
@admin_required
def edit_provider():
    p_id = request.form.get('id')
    name = request.form.get('name')
    api_key = request.form.get('api_key')
    base_url = request.form.get('base_url')
    max_conn = int(request.form.get('max_concurrent', 3))

    if db.update_provider(p_id, name, api_key, base_url, max_conn):
        flash('厂商信息更新成功', 'success')
    else:
        flash('更新失败', 'error')
    return redirect(url_for('admin.dashboard'))


@bp.route('/provider/delete/<int:p_id>')
@admin_required
def delete_provider(p_id):
    if db.delete_provider(p_id):
        flash('厂商及其模型已删除', 'success')
    return redirect(url_for('admin.dashboard'))


@bp.route('/provider/toggle/<int:p_id>/<int:state>')
@admin_required
def toggle_provider(p_id, state):
    db.toggle_provider(p_id, bool(state))
    return redirect(url_for('admin.dashboard'))


# --- AI Model Actions ---

@bp.route('/model/add', methods=['POST'])
@admin_required
def add_model():
    p_id = request.form.get('provider_id')
    name = request.form.get('model_name')
    capability = request.form.get('capability')
    weight = int(request.form.get('weight', 50))

    try:
        db.add_model(p_id, name, capability, weight)
        flash(f'模型 {name} 添加成功', 'success')
    except Exception as e:
        flash(f'添加失败: {str(e)}', 'error')

    return redirect(url_for('admin.dashboard'))


@bp.route('/model/edit', methods=['POST'])
@admin_required
def edit_model():
    m_id = request.form.get('id')
    name = request.form.get('model_name')
    capability = request.form.get('capability')
    weight = int(request.form.get('weight', 50))
    force_json = request.form.get('can_force_json') == 'on'

    if db.update_model(m_id, name, capability, weight, force_json):
        flash('模型更新成功', 'success')
    else:
        flash('更新失败', 'error')
    return redirect(url_for('admin.dashboard'))


@bp.route('/model/delete/<int:m_id>')
@admin_required
def delete_model(m_id):
    db.delete_model(m_id)
    flash('模型已删除', 'success')
    return redirect(url_for('admin.dashboard'))


@bp.route('/model/toggle/<int:m_id>/<int:state>')
@admin_required
def toggle_model(m_id, state):
    db.toggle_model(m_id, bool(state))
    return redirect(url_for('admin.dashboard'))
