import os
import json  # <---【1】记得添加 json 导入

from flask import Flask

from blueprints.admin import bp as admin_bp
from blueprints.ai_generator import bp as ai_gen_bp
from blueprints.auth import bp as auth_bp
from blueprints.export import bp as export_bp
from blueprints.grading import bp as grading_bp
from blueprints.library import bp as library_bp
from blueprints.main import bp as main_bp
from blueprints.signatures import bp as signatures_bp
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ---------------------------------------------------------
    # 【2】在此处重新注册模板过滤器 (Template Filters)
    # ---------------------------------------------------------

    def split_filter(s, delimiter=None):
        """自定义过滤器：字符串分割"""
        if not s:
            return []
        return s.split(delimiter)

    def from_json_filter(s):
        """自定义过滤器：解析 JSON 字符串"""
        if not s: return []
        try:
            return json.loads(s)
        except:
            return []

    # 将函数注册到 Jinja2 模板环境
    app.add_template_filter(split_filter, 'split')
    app.add_template_filter(from_json_filter, 'from_json')

    # ---------------------------------------------------------

    # 1. 确保目录存在
    for d in [
        app.config['UPLOAD_FOLDER'],
        app.config['WORKSPACE_FOLDER'],
        app.config['GRADERS_DIR'],
        app.config['TRASH_DIR'],
        app.config['FILE_REPO_FOLDER'],
        app.config['TEMPLATE_DIR'],
        app.config['SIGNATURES_FOLDER']
    ]:
        if not os.path.exists(d): os.makedirs(d)

    # 2. 初始化核心组件
    from grading_core.factory import GraderFactory
    try:
        GraderFactory.load_graders()
    except Exception as e:
        print(f"Startup Warning: {e}")

    # 3. 注册蓝图
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(grading_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(ai_gen_bp)
    app.register_blueprint(signatures_bp)
    app.register_blueprint(export_bp)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5010)
