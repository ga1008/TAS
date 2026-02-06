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
        返回所有可用策略的列表 (id, name, course)，用于前端下拉框

        Returns:
            list of tuples: [(grader_id, grader_name, course_name)]
            course_name: 使用 grader 的 COURSE 属性，如果不存在则返回 "未分类"
        """
        cls.load_graders()
        return [
            (k, v.NAME, getattr(v, 'COURSE', None) or '未分类')
            for k, v in cls._graders.items()
        ]