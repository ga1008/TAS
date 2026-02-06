import os
import json  # <---【1】记得添加 json 导入

from flask import Flask

from blueprints.admin import bp as admin_bp
from blueprints.ai_assistant import bp as ai_assistant_bp
from blueprints.ai_generator import bp as ai_gen_bp
from blueprints.ai_welcome import bp as ai_welcome_bp
from blueprints.auth import bp as auth_bp
from blueprints.export import bp as export_bp
from blueprints.grading import bp as grading_bp
from blueprints.library import bp as library_bp
from blueprints.main import bp as main_bp
from blueprints.notifications import bp as notifications_bp
from blueprints.signatures import bp as signatures_bp
from blueprints.student import bp as student_bp
from blueprints.jwxt import bp as jwxt_bp
from blueprints.stats import bp as stats_bp
from config import Config
from database import Database


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

    # 初始化全局数据库对象
    db = Database()

    # 优化 5: 注册请求销毁钩子
    @app.teardown_appcontext
    def close_db_connection(exception=None):
        """
        每个请求处理完成后执行。
        确保线程局部的 sqlite 连接被 close()，
        这样 SQLite 才能正确合并并删除 -shm 和 -wal 文件。
        """
        db.close()

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

    # 加载导出模板到数据库，如果数据库已有同名的模板则跳过
    # try:
    #     from blueprints.export import load_export_templates
    #     loaded_count = load_export_templates()
    #     if loaded_count > 0:
    #         print(f"[Startup] Loaded {loaded_count} export templates into the database.")
    # except Exception as e:
    #     print(f"Startup Warning (Export Templates): {e}")

    # 3. 清理旧的 AI 欢迎语记录 (30 天以上)
    try:
        from blueprints.ai_welcome import cleanup_old_welcome_messages
        cleaned = cleanup_old_welcome_messages(days=30)
        if cleaned > 0:
            print(f"[Startup] Cleaned {cleaned} old AI welcome records.")
    except Exception as e:
        print(f"Startup Warning (AI cleanup): {e}")

    # 4. 注册蓝图
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_assistant_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(grading_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(ai_gen_bp)
    app.register_blueprint(ai_welcome_bp)
    app.register_blueprint(signatures_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(jwxt_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(stats_bp)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5010)
