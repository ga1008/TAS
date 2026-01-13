import importlib.util
import inspect
import json
import os

from export_core.base_template import BaseExportTemplate
from extensions import db  # 假设 db 可以在这里引用，或者通过参数传入


class TemplateManager:
    _instances = {}

    @classmethod
    def load_templates(cls, template_dir):
        """
        扫描指定目录下的 .py 文件，自动加载继承自 BaseExportTemplate 的类
        并同步到数据库。
        """
        cls._instances = {}

        # 1. 扫描文件
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)

        for filename in os.listdir(template_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cls._load_single_file(os.path.join(template_dir, filename))

        # 2. 同步数据库状态 (可选：清理数据库中存在但文件已删除的记录)
        print(f"[TemplateManager] Loaded {len(cls._instances)} templates.")

    @classmethod
    def _load_single_file(cls, filepath):
        try:
            module_name = os.path.splitext(os.path.basename(filepath))[0]
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj) and issubclass(obj, BaseExportTemplate) and obj is not BaseExportTemplate:
                    # 注册到内存
                    cls._instances[obj.ID] = obj()
                    # 同步到数据库
                    cls._sync_to_db(obj, filepath)
        except Exception as e:
            print(f"[TemplateManager] Error loading {filepath}: {e}")

    @classmethod
    def _sync_to_db(cls, template_cls, filepath):
        """将模板信息（含 UI Schema）写入数据库，实现后端驱动前端"""
        conn = db.get_connection()
        schema_json = json.dumps(template_cls.UI_SCHEMA, ensure_ascii=False)

        # Upsert 逻辑
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM export_templates WHERE template_id=?", (template_cls.ID,))
        row = cursor.fetchone()

        if row:
            cursor.execute('''
                           UPDATE export_templates
                           SET name=?,
                               description=?,
                               file_path=?,
                               ui_schema=?,
                               updated_at=CURRENT_TIMESTAMP
                           WHERE template_id = ?
                           ''', (template_cls.NAME, template_cls.DESCRIPTION, filepath, schema_json, template_cls.ID))
        else:
            cursor.execute('''
                           INSERT INTO export_templates (template_id, name, description, file_path, ui_schema)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (template_cls.ID, template_cls.NAME, template_cls.DESCRIPTION, filepath, schema_json))
        conn.commit()

    @classmethod
    def get_template(cls, template_id):
        return cls._instances.get(template_id)

    @classmethod
    def get_all_metadata(cls):
        return [t.get_meta_dict() for t in cls._instances.values()]