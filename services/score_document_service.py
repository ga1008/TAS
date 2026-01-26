"""成绩文档自动生成服务

批改完成后自动将成绩同步到文档库，生成 Markdown 格式的成绩文档。
"""
import hashlib
import json
import logging
import re
from datetime import datetime

from extensions import db
from utils.academic_year import infer_academic_year_semester


def is_main_question(name: str) -> bool:
    """
    判断题目名称是否为大题

    大题规则:
    - 以中文数字开头 (一、二、三...)
    - 以 "第X" 格式开头 (第一、第二...)
    - 以 "任务X" 格式开头 (任务一、任务1...)

    小题规则:
    - 以阿拉伯数字开头 (1、2、1.1、2.1...)

    Args:
        name: 题目名称

    Returns:
        True if 大题, False if 小题
    """
    if not name or not isinstance(name, str):
        return False

    name = name.strip()

    # 中文数字: 一、二、三...
    if re.match(r'^[一二三四五六七八九十]+', name):
        return True

    # "第X" 格式: 第一、第二、第1、第2...
    if re.match(r'^第[一二三四五六七八九十\d]+', name):
        return True

    # 任务X 格式: 任务一、任务1...
    if re.match(r'^任务[一二三四五六七八九十\d]+', name):
        return True

    return False


def aggregate_main_questions(score_details):
    """
    从 score_details 中提取大题，聚合小题分数

    Args:
        score_details: 原始分项成绩列表 [{"name": "1.1", "score": 10}, ...]

    Returns:
        Tuple[main_scores, question_meta]:
        - main_scores: [{"name": "第一大题", "score": 30}, ...] 用于显示
        - question_meta: [{"name": "第一大题", "max_score": 30}, ...] 用于元数据
    """
    if not score_details or not isinstance(score_details, list):
        return [], []

    main_scores = []
    question_meta = []

    for item in score_details:
        if not isinstance(item, dict):
            continue

        name = item.get('name', '')
        score = item.get('score', 0)

        # 只保留大题
        if is_main_question(name):
            main_scores.append({
                'name': name,
                'score': score if score is not None else 0
            })
            question_meta.append({
                'name': name,
                'max_score': score if score is not None else 0
            })

    return main_scores, question_meta


class ScoreDocumentService:
    """成绩文档生成服务"""

    @staticmethod
    def generate_from_class(class_id, user_id):
        """
        批改完成后生成成绩文档到文档库

        Args:
            class_id: 班级 ID
            user_id: 触发生成的用户 ID

        Returns:
            dict: {'asset_id': int, 'filename': str} 成功时
            None: 无成绩或生成跳过时
        """
        try:
            # 1. 验证：至少有一个学生有成绩
            students = db.get_students_with_grades(class_id)
            graded = [s for s in students if s.get('total_score') is not None]
            if not graded:
                logging.info(f"[ScoreDoc] Class {class_id}: No graded students, skipping")
                return None

            # 2. 构建元数据
            metadata = ScoreDocumentService.build_metadata(class_id)

            # 3. 生成 Markdown
            content = ScoreDocumentService.build_markdown_content(class_id, metadata)

            # 4. 生成文件名（处理冲突）
            base_name = ScoreDocumentService._generate_filename(metadata)
            final_name = ScoreDocumentService._resolve_filename_conflict(class_id, base_name)

            # 5. 生成哈希
            timestamp = datetime.now().isoformat()
            file_hash = hashlib.sha256(
                f"{class_id}:{timestamp}:{content[:100]}".encode()
            ).hexdigest()

            # 6. 保存到 file_assets
            asset_id = db.save_score_document({
                'file_hash': file_hash,
                'original_name': final_name,
                'file_size': len(content.encode('utf-8')),
                'physical_path': None,
                'parsed_content': content,
                'meta_info': json.dumps(metadata, ensure_ascii=False),
                'doc_category': 'score_sheet',
                'course_name': metadata.get('course_name'),
                'source_class_id': class_id,
                'uploaded_by': user_id
            })

            logging.info(f"[ScoreDoc] Generated: {final_name} (ID: {asset_id})")
            return {'asset_id': asset_id, 'filename': final_name}

        except Exception as e:
            logging.error(f"[ScoreDoc] Generation failed for class {class_id}: {e}")
            return None

    @staticmethod
    def build_metadata(class_id):
        """
        构建成绩文档的元数据

        包含元数据追溯逻辑：
        class.strategy → ai_tasks.grader_id → ai_tasks.exam_path → file_assets.meta_info

        Args:
            class_id: 班级 ID

        Returns:
            dict: 元数据字典
        """
        # 获取班级信息
        cls = db.get_class_by_id(class_id)
        if not cls:
            raise ValueError(f"Class {class_id} not found")

        metadata = {
            'course_name': cls.get('course', ''),
            'class_name': cls.get('name', ''),
            'source_class_id': class_id,
            'generated_at': datetime.now().isoformat(),
        }

        # === 元数据追溯逻辑 (T019-T022) ===
        teacher = None
        course_code = None
        academic_year_semester = None

        # T019: 从 class.strategy 追溯到 ai_tasks
        grader_id = cls.get('strategy')
        if grader_id:
            task = db.get_task_by_grader_id(grader_id)
            if task:
                # T020: 获取 exam_path 并查找对应的 file_assets
                exam_path = task.get('exam_path')
                if exam_path:
                    exam_asset = db.get_file_asset_by_path(exam_path)
                    if exam_asset and exam_asset.get('meta_info'):
                        # T021: 从 exam file 的 meta_info 提取 teacher 和 course_code
                        try:
                            exam_meta = json.loads(exam_asset['meta_info'])
                            if isinstance(exam_meta, dict):
                                teacher = exam_meta.get('teacher')
                                course_code = exam_meta.get('course_code')
                                # 也尝试获取学年学期
                                academic_year_semester = exam_meta.get('academic_year_semester')
                        except (json.JSONDecodeError, TypeError):
                            pass

        # T022: 学年学期 fallback - 使用推断函数
        if not academic_year_semester:
            academic_year_semester = infer_academic_year_semester()

        metadata['teacher'] = teacher
        metadata['course_code'] = course_code
        metadata['academic_year_semester'] = academic_year_semester
        # === END 元数据追溯逻辑 ===

        # 统计信息
        students = db.get_students_with_grades(class_id)
        graded = [s for s in students if s.get('total_score') is not None]
        passed = [s for s in graded if s.get('status') == 'PASS' or (s.get('total_score') or 0) >= 60]

        metadata['student_count'] = len(students)
        metadata['graded_count'] = len(graded)
        if graded:
            total = sum(s.get('total_score', 0) or 0 for s in graded)
            metadata['average_score'] = round(total / len(graded), 2)
            metadata['pass_rate'] = round(len(passed) / len(graded), 2)
        else:
            metadata['average_score'] = 0
            metadata['pass_rate'] = 0

        # === 大题分数元数据 (T005) ===
        # 从第一个有 score_details 的学生获取大题信息
        question_scores = []
        for s in graded:
            if s.get('score_details'):
                try:
                    details = json.loads(s['score_details'])
                    if isinstance(details, list):
                        _, question_scores = aggregate_main_questions(details)
                        break
                except (json.JSONDecodeError, TypeError):
                    pass

        metadata['question_scores'] = question_scores
        metadata['total_max_score'] = sum(q.get('max_score', 0) for q in question_scores) if question_scores else 0
        # === END 大题分数元数据 ===

        return metadata

    @staticmethod
    def build_markdown_content(class_id, metadata):
        """
        生成 Markdown 格式的成绩文档

        Args:
            class_id: 班级 ID
            metadata: 元数据字典

        Returns:
            str: Markdown 内容
        """
        students = db.get_students_with_grades(class_id)
        if not students:
            raise ValueError(f"No students found for class {class_id}")

        # 构建文档头部
        lines = [
            "# 机考成绩表",
            "",
            f"**课程**: {metadata.get('course_name', '')}" +
            (f" ({metadata.get('course_code', '')})" if metadata.get('course_code') else ""),
            f"**班级**: {metadata.get('class_name', '')}",
        ]

        if metadata.get('teacher'):
            lines.append(f"**教师**: {metadata['teacher']}")

        lines.extend([
            f"**学期**: {metadata.get('academic_year_semester', '')}",
            f"**生成时间**: {metadata.get('generated_at', '')[:19].replace('T', ' ')}",
            "",
            f"**统计**: 共 {metadata.get('student_count', 0)} 人，"
            f"已批改 {metadata.get('graded_count', 0)} 人，"
            f"平均分 {metadata.get('average_score', 0)}，"
            f"及格率 {metadata.get('pass_rate', 0) * 100:.1f}%",
            "",
        ])

        # 获取分项成绩列名（从第一个有成绩的学生获取）- 仅保留大题 (T006)
        score_columns = []
        for s in students:
            if s.get('score_details'):
                try:
                    details = json.loads(s['score_details'])
                    if isinstance(details, list):
                        # 仅保留大题列名
                        score_columns = [
                            d.get('name', f'题{i+1}')
                            for i, d in enumerate(details)
                            if is_main_question(d.get('name', ''))
                        ]
                        break
                except:
                    pass

        # 构建表头
        header = "| 序号 | 学号 | 姓名 | 性别 |"
        separator = "|------|------|------|------|"
        for col in score_columns:
            header += f" {col} |"
            separator += "------|"
        header += " 总分 | 状态 |"
        separator += "------|------|"

        lines.append(header)
        lines.append(separator)

        # 填充数据行
        for idx, s in enumerate(students):
            student_id = s.get('student_id', '')
            name = s.get('name', '')
            gender = s.get('gender', '') or '-'

            # 解析分项成绩 - 仅保留大题 (T006)
            scores = {}
            if s.get('score_details'):
                try:
                    details = json.loads(s['score_details'])
                    if isinstance(details, list):
                        for i, d in enumerate(details):
                            col_name = d.get('name', f'题{i+1}')
                            # 仅保留大题分数
                            if is_main_question(col_name):
                                scores[col_name] = d.get('score', '-')
                except:
                    pass

            total = s.get('total_score')
            total_str = str(int(total)) if total is not None else '-'

            status = s.get('status', '')
            if status == 'PASS':
                status_str = '通过'
            elif status == 'ERROR':
                status_str = '批改失败'
            elif total is not None:
                status_str = '已批改'
            else:
                status_str = '未批改'

            row = f"| {idx + 1} | {student_id} | {name} | {gender} |"
            for col in score_columns:
                row += f" {scores.get(col, '-')} |"
            row += f" {total_str} | {status_str} |"

            lines.append(row)

        return "\n".join(lines)

    @staticmethod
    def _generate_filename(metadata):
        """
        生成成绩文档文件名

        格式: {学年学期}-{课程名}-{班级名}-机考分数.md

        Args:
            metadata: 元数据字典

        Returns:
            str: 文件名
        """
        parts = [
            metadata.get('academic_year_semester', ''),
            metadata.get('course_name', ''),
            metadata.get('class_name', ''),
            '机考分数'
        ]
        # 过滤空值
        parts = [p for p in parts if p]
        return '-'.join(parts) + '.md'

    @staticmethod
    def _resolve_filename_conflict(class_id, base_name):
        """
        处理文件名冲突，如果已存在则添加时间戳后缀

        Args:
            class_id: 班级 ID
            base_name: 基础文件名

        Returns:
            str: 最终文件名
        """
        # 检查是否已有该班级的成绩文档
        count = db.count_score_documents_for_class(class_id)
        if count > 0:
            # 添加时间戳后缀
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            name_without_ext = base_name.rsplit('.', 1)[0]
            ext = base_name.rsplit('.', 1)[1] if '.' in base_name else 'md'
            return f"{name_without_ext}_{timestamp}.{ext}"
        return base_name
