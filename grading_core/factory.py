# grading_core/factory.py
import importlib
import inspect
import pkgutil
import sys

from config import Config
from grading_core.base import BaseGrader


class GraderFactory:
    _graders = {}
    _loaded = False

    @classmethod
    def load_graders(cls):
        """动态加载 graders 目录下的所有模块 (支持热重载)"""
        # 每次加载前清空当前字典，确保加载的是最新状态
        cls._graders = {}

        # 遍历包下的所有模块
        for _, name, _ in pkgutil.iter_modules([Config.GRADERS_DIR]):
            module_name = f'grading_core.graders.{name}'
            try:
                # === 核心修改：热重载逻辑 ===
                if module_name in sys.modules:
                    # 如果模块已存在缓存中，强制重载
                    module = importlib.reload(sys.modules[module_name])
                else:
                    # 首次导入
                    module = importlib.import_module(module_name)

                # 检查模块中的所有类
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)

                    # 如果是 BaseGrader 的子类，且不是 BaseGrader 本身
                    if (inspect.isclass(attribute) and
                            issubclass(attribute, BaseGrader) and
                            attribute is not BaseGrader):
                        # 注册到字典中
                        cls._graders[attribute.ID] = attribute
                        # print(f"Loaded/Reloaded grader: {attribute.NAME} ({attribute.ID})")
            except Exception as e:
                print(f"Failed to load grader module {name}: {e}")

        cls._loaded = True

    @classmethod
    def get_grader(cls, strategy_id):
        cls.load_graders()
        grader_class = cls._graders.get(strategy_id)
        if grader_class:
            return grader_class()
        # 默认返回第一个或报错，这里做简单处理
        return None

    @classmethod
    def get_all_strategies(cls):
        """
        返回所有可用策略的详细列表，包含数据库元数据

        Returns:
            list of dict: [{
                'id': grader_id,
                'name': display_name,
                'course': course_name,
                'description': extra_desc,
                'strictness': strictness,
                'type': 'logic' | 'direct',
                'created_at': timestamp,
                'creator': creator_name
            }]
        """
        cls.load_graders()
        strategies = []

        # 引入 DB 避免循环导入
        from extensions import db

        # 获取所有任务信息用于增强展示
        # 这里为了性能，可以只查 ai_tasks 表
        conn = db.get_connection()
        tasks = conn.execute(
            "SELECT grader_id, extra_desc, strictness, created_at, created_by, status FROM ai_tasks WHERE status='success'").fetchall()
        task_map = {t['grader_id']: dict(t) for t in tasks if t['grader_id']}

        # 获取用户名映射
        users = conn.execute("SELECT id, username FROM users").fetchall()
        user_map = {u['id']: u['username'] for u in users}

        for grader_id, grader_cls in cls._graders.items():
            # 基础信息来自 Python 类
            info = {
                'id': grader_id,
                'name': getattr(grader_cls, 'NAME', grader_id),
                'course': getattr(grader_cls, 'COURSE', '未分类'),
                'description': '系统内置或无描述',
                'strictness': 'standard',
                'type': 'logic',  # 默认为 logic, direct 会被覆盖
                'created_at': '',
                'creator': 'System'
            }

            # 尝试判断类型
            if getattr(grader_cls, 'is_ai_grader', False) or 'DirectGrader' in grader_cls.__name__:
                info['type'] = 'direct'

            # 融合数据库信息
            task_info = task_map.get(grader_id)
            if task_info:
                info['description'] = task_info.get('extra_desc') or '暂无额外描述'
                info['strictness'] = task_info.get('strictness', 'standard')
                info['created_at'] = task_info.get('created_at', '')

                creator_id = task_info.get('created_by')
                if creator_id:
                    info['creator'] = user_map.get(creator_id, 'Unknown')

                # 如果是 Direct 类型，确保类型标识正确
                if 'direct' in grader_id:
                    info['type'] = 'direct'

            strategies.append(info)

        # 按创建时间倒序
        strategies.sort(key=lambda x: x['created_at'] or '0', reverse=True)
        return strategies