from flask import Blueprint, render_template, request, redirect, url_for, session, g

from extensions import db

bp = Blueprint('auth', __name__)


@bp.before_app_request
def load_logged_in_user():
    user_info = session.get('user')
    if user_info:
        conn = db.get_connection()
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_info['id'],)).fetchone()
        g.user = dict(user) if user else None
    else:
        g.user = None


@bp.before_app_request
def auth_middleware():
    if request.endpoint in ['auth.login', 'auth.logout', 'static', 'main.intro']:
        return None
    if request.path.startswith('/admin'):  # Admin blueprint handle itself
        return None
    if not g.user:
        return redirect(url_for('auth.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            return render_template('login.html', error="请输入用户名")
        user = db.login_simple_user(username)
        session['user'] = user
        return redirect(url_for('main.index'))
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login'))
