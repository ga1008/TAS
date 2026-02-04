# services/grading_service.py
import logging
import os
import shutil

import patoolib
# [NEW] 引入并发库和系统库
import concurrent.futures
import multiprocessing

from extensions import db
from grading_core.factory import GraderFactory
from services.file_service import FileService

# 配置日志
logger = logging.getLogger(__name__)


class GradingService:

    # [NEW] 新增：批量并发批改入口
    @staticmethod
    def grade_all_students(class_id):
        """
        并发批改全班作业
        :param class_id: 班级ID
        :return: (success_count, fail_count, total_count)
        """
        # 1. 获取班级和学生信息
        cls_info = db.get_class_by_id(class_id)
        if not cls_info:
            return 0, 0, 0

        students = db.get_students_with_grades(class_id)
        if not students:
            return 0, 0, 0

        # 2. 加载评分策略，判断并发模式
        strategy_name = cls_info.get('strategy', '')
        grader = GraderFactory.get_grader(strategy_name)

        max_workers = 1
        concurrency_mode = "Serial"

        if grader:
            if getattr(grader, 'is_ai_grader', False):
                # A. AI 模式：从数据库读取厂商限制
                provider_id = getattr(grader, 'ai_provider_id', None)
                limit = db.get_provider_concurrency(provider_id)
                # 限制最大线程数，防止爆内存
                max_workers = min(limit, 10)
                concurrency_mode = f"AI Provider Limit (ID:{provider_id})"
            else:
                # B. 逻辑核心模式：根据 CPU 核心数动态调整
                # 逻辑批改通常是 CPU/IO 混合型，设置为 CPU 核心数 + 2 是常见实践
                try:
                    cpu_count = multiprocessing.cpu_count()
                    # 至少给系统留一点余地，但也至少保证有2个线程
                    max_workers = max(2, cpu_count + 1)
                except:
                    max_workers = 4
                concurrency_mode = "Dynamic CPU"

        logger.info(f"Class {class_id} grading started. Mode: {concurrency_mode}, Workers: {max_workers}")

        # 3. 构造任务列表
        # 过滤掉不需要批改的学生？通常是全量覆盖或者前端传参，这里假设是对所有学生进行批改
        # 如果需要只批改未交的，可以在这里过滤
        student_ids = [s['student_id'] for s in students]

        success_count = 0
        fail_count = 0

        # 4. 执行并发批改
        # 使用 ThreadPoolExecutor，因为涉及大量文件IO和可能的DB等待
        # SQLite 在 database.py 中已经配置了 local connection，是线程安全的
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务字典 {future: student_id}
            future_to_sid = {
                executor.submit(GradingService.grade_single_student, class_id, sid): sid
                for sid in student_ids
            }

            for future in concurrent.futures.as_completed(future_to_sid):
                sid = future_to_sid[future]
                try:
                    is_ok, msg, _ = future.result()
                    if is_ok:
                        success_count += 1
                    else:
                        fail_count += 1
                        # 可以选择记录更详细的日志
                except Exception as exc:
                    logger.error(f"Unhandled exception for student {sid}: {exc}")
                    fail_count += 1

        return success_count, fail_count, len(students)

    @staticmethod
    def grade_single_student(class_id, student_id):
        """核心批改逻辑 (保持不变，作为原子 Worker 被调用)"""
        # 注意：db.get_connection() 使用了 threading.local()，
        # 所以在不同线程中调用此函数时，会获取独立的数据库连接，保证线程安全。

        cls_info = db.get_class_by_id(class_id)
        if not cls_info: return False, "班级不存在", None

        ws_path = FileService.get_real_workspace_path(class_id)
        raw_dir = os.path.join(ws_path, 'raw_zips')
        extract_base = os.path.join(ws_path, 'extracted')

        # [Thread Safety Check]
        # get_student_detail 内部如果是单例 cursor 可能会有问题。
        # database.py 的 get_student_detail 实际上是 create_connection -> query -> return dict
        # 只要 database.py 里的 helper 是每次 execute 拿 connection，就是安全的。
        # 你的 database.py get_connection 用了 threading.local，所以这里是安全的。

        student = db.get_student_detail(class_id, student_id)
        if not student:
            # 兼容性 Fallback
            conn = db.get_connection()
            student = conn.execute("SELECT * FROM students WHERE class_id=? AND student_id=?",
                                   (class_id, student_id)).fetchone()

        if not student: return False, "找不到学生", None
        name = student['name']

        # 查找文件
        if not os.path.exists(raw_dir): return False, "无上传文件", None
        matched_file = None
        # [Performance] os.listdir 在高并发下略慢，但对于几百个文件通常没问题
        for f in os.listdir(raw_dir):
            if str(student_id) in f or name in f:
                matched_file = f
                break

        if not matched_file:
            db.save_grade_error(student_id, class_id, "未找到提交文件", "")
            return False, "未找到提交文件", None

        # 解压
        # [Thread Safety] 每个学生有独立的 extract 目录，互不冲突，安全。
        student_extract_dir = os.path.join(extract_base, str(student_id))
        if os.path.exists(student_extract_dir):
            try:
                shutil.rmtree(student_extract_dir)
            except:
                pass
        os.makedirs(student_extract_dir, exist_ok=True)

        try:
            archive_path = os.path.join(raw_dir, matched_file)

            # [Optimization]
            # GraderFactory.get_grader 内部有 importlib.reload。
            # 在多线程下频繁 reload 可能会有锁竞争或性能损耗。
            # 但考虑到 batch_grade_all 已经在外部获取了一次 grader 实例用于判断并发，
            # 这里再次获取是实例化一个新对象（grader通常是无状态或轻状态的），这是正确的。
            grader = GraderFactory.get_grader(cls_info['strategy'])
            if not grader: return False, "评分策略加载失败", matched_file

            try:
                # patoolib 内部通常调用外部 7z/unrar 进程，并发执行是安全的
                patoolib.extract_archive(archive_path, outdir=student_extract_dir, verbosity=-1)
            except Exception as e:
                # 简单的异常处理，不影响其他线程
                if "rar" in matched_file.lower(): raise Exception("解压RAR失败，请检查服务器组件")
                raise e

            # 调用 AI 批改核心 / 逻辑核心
            # 这里的 grader.grade 必须要保证线程安全。
            # 如果是 AI 核心，它会调用 request，本身就是阻塞IO，适合多线程。
            result = grader.grade(student_extract_dir, {"sid": str(student_id), "name": name})

            status = "PASS" if result.is_pass else "FAIL"

            # [Thread Safety] SQLite Write
            # SQLite 只有一个写锁。WAL 模式下并发读写性能较好，但高并发写入仍可能 lock timeout。
            # database.py 设置了 timeout=30.0，一般足够。
            # 如果出现 database is locked，可以将 save_grade 放入队列由主线程统一写，但目前的规模直接写更简单。
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