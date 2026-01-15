from flask import Blueprint, render_template, g

from extensions import db

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    classes = db.get_classes(user_id=g.user['id'])
    return render_template('index.html', classes=classes, user=g.user)


@bp.route('/intro')
def intro():
    return render_template('intro.html')
