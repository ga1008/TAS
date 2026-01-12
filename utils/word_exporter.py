# utils/word_exporter.py
from utils.word_exporter_exam import GuangWaiExamExporter
from utils.word_exporter_standard import GuangWaiStandardExporter


class ExamWordExporter:
    """
    Facade class to maintain backward compatibility and route requests.
    """

    def __init__(self, template_type="exam_guangwai"):
        self.template_type = template_type

    def generate_guangwai_exam(self, content, metadata, output_path):
        """
        统一入口方法
        """
        if self.template_type == "grading_standard":
            exporter = GuangWaiStandardExporter()
            return exporter.generate(content, metadata, output_path)
        else:
            # 默认回退到试卷导出
            exporter = GuangWaiExamExporter()
            return exporter.generate(content, metadata, output_path)
