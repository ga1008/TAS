# services/grading_service.py
import os
import shutil

import patoolib

from extensions import db
from grading_core.factory import GraderFactory
from services.file_service import FileService


class GradingService:
    @staticmethod
    def grade_single_student(class_id, student_id):
        """核心批改逻辑"""
        cls_info = db.get_class_by_id(class_id)
        if not cls_info: return False, "班级不存在", None

        ws_path = FileService.get_real_workspace_path(class_id)
        raw_dir = os.path.join(ws_path, 'raw_zips')
        extract_base = os.path.join(ws_path, 'extracted')

        student = db.get_student_detail(class_id, student_id)  # 这里的SQL需要确认db有这个方法
        # 如果 database.py 里没有 get_student_detail，可以用 get_connection 手写查询
        # 为了兼容，我们假设有，或者这里手动查
        if not student:
            conn = db.get_connection()
            student = conn.execute("SELECT * FROM students WHERE class_id=? AND student_id=?",
                                   (class_id, student_id)).fetchone()

        if not student: return False, "找不到学生", None
        name = student['name']

        # 查找文件
        if not os.path.exists(raw_dir): return False, "无上传文件", None
        matched_file = None
        for f in os.listdir(raw_dir):
            if str(student_id) in f or name in f:
                matched_file = f
                break

        if not matched_file:
            db.save_grade_error(student_id, class_id, "未找到提交文件", "")
            return False, "未找到提交文件", None

        # 解压
        student_extract_dir = os.path.join(extract_base, str(student_id))
        if os.path.exists(student_extract_dir):
            try:
                shutil.rmtree(student_extract_dir)
            except:
                pass
        os.makedirs(student_extract_dir, exist_ok=True)

        try:
            archive_path = os.path.join(raw_dir, matched_file)
            grader = GraderFactory.get_grader(cls_info['strategy'])
            if not grader: return False, "评分策略加载失败", matched_file

            try:
                patoolib.extract_archive(archive_path, outdir=student_extract_dir, verbosity=-1)
            except Exception as e:
                if "rar" in matched_file.lower(): raise Exception("解压RAR失败，请检查服务器组件")
                raise e

            # 调用 AI 批改核心
            result = grader.grade(student_extract_dir, {"sid": str(student_id), "name": name})

            status = "PASS" if result.is_pass else "FAIL"
            db.save_grade(str(student_id), class_id, result.total_score, result.get_details_json(),
                          result.get_deduct_str(), status, matched_file)

            return True, "批改完成", {
                "total_score": result.total_score,
                "status": status,
                "details": result.sub_scores
            }

        except Exception as e:
            msg = f"系统异常: {str(e)}"
            db.save_grade_error(str(student_id), class_id, msg, matched_file)
            return False, msg, matched_file
