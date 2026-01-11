from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from extensions import db

bp = Blueprint('auth', __name__)


@bp.before_app_request
def load_logged_in_user():
    user_json = session.get('user')
    g.user = user_json if user_json else None


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('main.index'))
        # ... 原有登录逻辑 ...
    # 注意：db.get_or_create_user(username) 调用保持不变


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
