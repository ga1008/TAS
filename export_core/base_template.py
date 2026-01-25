import abc


class BaseExportTemplate(abc.ABC):
    ID = "base"
    NAME = "Base Template"
    DESCRIPTION = "基础模板"

    # [新增] 定义导出文件的扩展名，默认为 docx，Excel 模板需重写为 xlsx
    FILE_EXTENSION = "docx"

    # 定义前端需要渲染的表单字段 (UI Schema)
    # 类型支持: text, date, number, select, signature_selector, hidden
    UI_SCHEMA = []

    def get_meta_dict(self):
        """返回模板的元数据字典"""
        return {
            "id": self.ID,
            "name": self.NAME,
            "description": self.DESCRIPTION,
            "schema": self.UI_SCHEMA,
            "extension": self.FILE_EXTENSION  # 告知前端或后端此模板的文件类型
        }

    @abc.abstractmethod
    def generate(self, content: str, meta_info: dict, form_data: dict, output_path: str):
        """
        :param content: 解析后的 Markdown 正文
        :param meta_info: 文件入库时 AI 提取的元数据 (用于兜底)
        :param form_data: 前端表单提交的数据 (用户手动填写或确认的数据)
        :param output_path: 结果保存路径
        """
        pass