# utils/word_exporter_base.py
import re
from datetime import datetime
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


class BaseWordExporter:
    def __init__(self):
        self.doc = Document()

        # === 字体常量 ===
        self.FONT_CN_MAIN = '宋体'
        self.FONT_CN_BOLD = '黑体'  # 很多正式文档标题用黑体，正文粗体用宋体加粗
        self.FONT_EN = 'Times New Roman'

        # === 字号映射 (Pt) ===
        self.SIZE_SMALL_2 = 18  # 小二
        self.SIZE_4 = 14  # 四号
        self.SIZE_SMALL_4 = 12  # 小四
        self.SIZE_5 = 10.5  # 五号
        self.SIZE_SMALL_5 = 9  # 小五

    def setup_page(self, margin_top=1.5, margin_bottom=1.5, margin_left=1.5, margin_right=1.5, footer_distance=1.75):
        """通用页面设置，默认参数适配评分细则"""
        section = self.doc.sections[0]
        section.page_width = Cm(21)  # A4 Width
        section.page_height = Cm(29.7)  # A4 Height
        section.top_margin = Cm(margin_top)
        section.bottom_margin = Cm(margin_bottom)
        section.left_margin = Cm(margin_left)
        section.right_margin = Cm(margin_right)
        section.footer_distance = Cm(footer_distance)
        return section

    def set_font(self, run, size_pt, bold=False, font_name='宋体', align=None, underline=False):
        """统一字体设置"""
        if not run: return
        run.font.name = self.FONT_EN
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
        run.font.size = Pt(size_pt)
        run.font.bold = bold
        run.font.underline = underline
        run.font.color.rgb = RGBColor(0, 0, 0)

    def clean_markdown(self, text):
        """清洗 Markdown 标记"""
        if not text: return ""
        # 去除标题标记 (#)
        text = re.sub(r'^#+\s*', '', text)
        # 去除加粗/斜体 (**, __, *, _)
        text = re.sub(r'[\*\_]{1,2}', '', text)
        # 去除列表标记 (-, +) 在行首的情况
        text = re.sub(r'^[\-\+]\s+', '', text)
        # 去除代码块标记 (`)
        text = re.sub(r'`+', '', text)
        return text.strip()

    def get_semester_info(self):
        """计算学年和学期"""
        now = datetime.now()
        year = now.year
        month = now.month

        # 逻辑：
        # 2月-7月 -> 属于 (Year-1)-(Year) 第二学期
        # 8月-1月 -> 属于 (Year)-(Year+1) 第一学期
        if 2 <= month <= 7:
            y_start = year - 1
            y_end = year
            semester = "二"
        else:
            y_start = year
            y_end = year + 1
            semester = "一"

        return str(y_start), str(y_end), semester

    def add_page_number_field(self, paragraph):
        """插入页码：单数字"""
        self.add_field(paragraph, "PAGE")

    def add_field(self, paragraph, field_code):
        run = paragraph.add_run()
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = field_code
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        run._element.append(fldChar1)
        run._element.append(instrText)
        run._element.append(fldChar2)
        self.set_font(run, self.SIZE_SMALL_5)