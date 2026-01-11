# grading_core/base.py
import json
import os
import re
import abc


class GradingResult:
    """标准化的评分结果对象"""

    def __init__(self):
        self.total_score = 0
        self.is_pass = False
        self.deduct_details = []

        # --- 数据库兼容字段 ---
        # 虽然基类不应限制题目数量，但为了兼容现有的 SQLite 表结构 (task1_score, task2_score)，
        # 我们保留这两个字段作为"分桶"。
        # AI 在生成代码时，可以将"基础题"汇总入 task1，"提高题"汇总入 task2。
        self.sub_scores = []

    def add_sub_score(self, name, score, *args, **kwargs):
        """
        添加一个评分细项
        :param name: 题目名称 (如 'Task 1: 环境配置')
        :param score: 该项得分
        """
        # 确保分数为数字
        try:
            score = float(score)
        except:
            score = 0

        self.sub_scores.append({
            "name": name,
            "score": score
        })

    def get_deduct_str(self, *args, **kwargs):
        return "; ".join(self.deduct_details) if self.deduct_details else ""

    def get_details_json(self, *args, **kwargs):
        """序列化为 JSON 字符串存入数据库"""
        return json.dumps(self.sub_scores, ensure_ascii=False)

    def add_deduction(self, msg, *args, **kwargs):
        self.deduct_details.append(msg)


class BaseGrader(abc.ABC):
    """
    抽象基类：所有科目的批改器必须继承此类

    V2.0 改进：内置了智能文件查找、正则校验等通用工具，
    生成的子类只需关注业务逻辑，无需重复实现底层代码。
    """

    ID = "base"
    NAME = "Base Grader"

    def __init__(self):
        self.file_map = {}  # 文件名索引 {lowercase_name: full_path}

    @abc.abstractmethod
    def grade(self, student_dir, student_info, *args, **kwargs) -> GradingResult:
        """核心批改逻辑接口"""
        pass

    # ==========================================================================
    # 通用工具方法 (供 AI 生成的子类直接调用)
    # ==========================================================================

    def scan_files(self, root_dir, *args, **kwargs):
        """
        初始化文件索引：全盘扫描，建立 {文件名(小写): 绝对路径} 的映射
        解决层级过深、大小写不规范等问题。
        必须在 grade() 开头调用一次。
        """
        self.file_map = {}
        for root, _, files in os.walk(root_dir):
            for f in files:
                self.file_map[f.lower()] = os.path.join(root, f)
        return self.file_map

    def smart_find(self, target_filename, alternatives=None, ignore_subfixes=False, *args, **kwargs):
        """
        智能查找文件
        :param target_filename: 目标文件名 (如 10.png)
        :param alternatives: 允许的替代文件名列表 (如 ['10-1.png'])
        :param ignore_subfixes: 是否忽略后缀大小写
        :return: (file_path, penalty_score) -> (路径, 扣分值)
        """
        if not self.file_map:
            raise RuntimeError("File map not initialized. Call self.scan_files(student_dir) first.")

        penalty = 0
        target_lower = target_filename.lower()

        # 1. 精确/忽略大小写匹配
        if target_lower in self.file_map:
            real_path = self.file_map[target_lower]
            real_name = os.path.basename(real_path)
            # Linux下文件名大小写敏感，如果要求严格但学生大小写不对，建议扣1分
            if not ignore_subfixes and real_name != target_filename:
                penalty = 1
            return real_path, penalty

        # 2. 替代名匹配 (宽容模式)
        if alternatives:
            for alt in alternatives:
                if alt.lower() in self.file_map:
                    return self.file_map[alt.lower()], 1  # 用了别名，通常扣1分规范分

        return None, 0

    def read_text_content(self, file_path, *args, **kwargs):
        """健壮的文本读取，自动尝试多种编码"""
        if not file_path or not os.path.exists(file_path):
            return None

        encodings = ['utf-8', 'gbk', 'cp936', 'latin-1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except:
                continue
        return None

    def verify_command(self, content, result_obj: GradingResult,
                       strict_regex, loose_regex, full_pts, name, *args, **kwargs):
        """
        命令/代码双重验证引擎
        :param content: 文件内容
        :param result_obj: 结果对象 (用于记录扣分详情)
        :param strict_regex: 严格匹配正则 (得满分)
        :param loose_regex: 宽容匹配正则 (得一半分)
        :param full_pts: 该项满分值
        :param name: 检查项名称
        :return: 实际得分
        """
        if not content:
            return 0

        # 1. 严格匹配
        if re.search(strict_regex, content, re.IGNORECASE | re.MULTILINE):
            return full_pts

        # 2. 宽容匹配 (如果不为空)
        if loose_regex and re.search(loose_regex, content, re.IGNORECASE | re.MULTILINE):
            half_pts = max(1, full_pts // 2)
            result_obj.add_deduction(f"{name}:命令/参数不完整或有误(得{half_pts}分)")
            return half_pts

        # 3. 失败
        result_obj.add_deduction(f"{name}:未检测到有效关键命令(-{full_pts})")
        return 0