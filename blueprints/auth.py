import functools
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, session
from extensions import db  # 引用单例

bp = Blueprint('admin', __name__, url_prefix='/admin')


# === 权限控制 ===
def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or not g.user.get('is_admin'):
            return redirect(url_for('auth.login'))  # 假设 auth 蓝图存在，或者跳转到 admin.login
        return view(**kwargs)

    return wrapped_view


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.verify_admin_login(username, password)
        if user:
            session.clear()
            session['user'] = user
            return redirect(url_for('admin.dashboard'))
        flash('管理员账号或密码错误', 'error')
    return render_template('login.html')  # 复用你上传的 login.html


@bp.route('/')
@admin_required
def dashboard():
    providers = db.get_all_providers()
    for p in providers:
        p['models'] = db.get_models_by_provider(p['id'])
    return render_template('dashboard.html', providers=providers)  # 复用你上传的 dashboard.html


# === 厂商管理 API ===

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
        flash('更新成功', 'success')
    else:
        flash('更新失败', 'error')
    return redirect(url_for('admin.dashboard'))


@bp.route('/provider/delete/<int:p_id>')
@admin_required
def delete_provider(p_id):
    db.delete_provider(p_id)
    flash('厂商已删除', 'success')
    return redirect(url_for('admin.dashboard'))


@bp.route('/provider/toggle/<int:p_id>/<int:state>')
@admin_required
def toggle_provider(p_id, state):
    db.toggle_provider(p_id, bool(state))
    return redirect(url_for('admin.dashboard'))


# === 模型管理 API ===

@bp.route('/model/add', methods=['POST'])
@admin_required
def add_model():
    p_id = request.form.get('provider_id')
    name = request.form.get('model_name')
    capability = request.form.get('capability')
    weight = int(request.form.get('weight', 50))
    try:
        db.add_model(p_id, name, capability, weight)
        flash('模型添加成功', 'success')
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
    db.update_model(m_id, name, capability, weight, force_json)
    flash('模型更新成功', 'success')
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
