import mimetypes
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed # 引入线程池

import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file, g

from config import Config
from extensions import db
from export_core.filename_generator import get_export_filename
from grading_core.factory import GraderFactory
from services.file_service import FileService
from services.grading_service import GradingService
from services.score_document_service import ScoreDocumentService

bp = Blueprint('grading', __name__)


@bp.route('/new_class', methods=['GET', 'POST'])
def new_class():
    if request.method == 'POST':
        cname = request.form.get('class_name', '').strip()
        course = request.form.get('course_name', '').strip()
        strategy = request.form.get('strategy', '')
        student_list_id = request.form.get('student_list_id', '').strip()

        if cname and course:
            # 创建班级记录
            cid = db.create_class(cname, course, strategy, g.user['id'])
            FileService.get_real_workspace_path(cid)
            db.update_class_workspace(cid, FileService.get_real_workspace_path(cid))

            # 如果选择了学生名单，则导入学生
            if student_list_id:
                try:
                    # 从 student_details 表获取学生列表（包含状态信息）
                    students = db.get_student_details(student_list_id)

                    # 只导入状态为 normal 的学生
                    imported_count = 0
                    for student in students:
                        # 跳过状态为 abnormal 的学生
                        if student.get('status') == 'abnormal':
                            continue

                        if student.get('student_id') and student.get('name'):
                            # 检查是否已存在
                            existing = db.get_student_detail(cid, student['student_id'])
                            if not existing:
                                db.add_student(
                                    student_id=student['student_id'],
                                    name=student['name'],
                                    class_id=cid
                                )
                                imported_count += 1

                    print(f"成功导入 {imported_count} 名学生到班级 {cname}")

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    # 学生导入失败不影响班级创建，只记录错误
                    print(f"学生导入失败: {e}")

            # 刷新 AI 欢迎语缓存（在用户创建班级后）
            try:
                from services.ai_content_service import invalidate_cache
                invalidate_cache(g.user['id'], 'dashboard')
            except Exception as e:
                print(f"[AI Welcome] Cache refresh failed: {e}")

            return redirect(url_for('grading.grading_view', class_id=cid))

    GraderFactory.load_graders()
    strategies = GraderFactory.get_all_strategies()
    return render_template('newClass.html', strategies=strategies, user=g.user)


@bp.route('/grading/<int:class_id>')
def grading_view(class_id):
    cls = db.get_class_by_id(class_id)
    if not cls or cls['created_by'] != g.user['id']: return "Unauthorized", 403

    GraderFactory.load_graders()
    grader = GraderFactory.get_grader(cls['strategy'])
    grader_name = grader.NAME if grader else "未知核心或核心已删除"

    students = db.get_students_with_grades(class_id)
    return render_template('grading.html', cls=cls, students=students, user=g.user, grader_name=grader_name, strategy=cls['strategy'])


@bp.route('/api/grade_student/<int:class_id>/<string:student_id>', methods=['POST'])
def api_grade_student(class_id, student_id):
    success, msg, data = GradingService.grade_single_student(class_id, student_id)

    # 刷新 AI 欢迎语缓存（在用户批改学生作业后）
    if success and g.user:
        try:
            from services.ai_content_service import invalidate_cache
            invalidate_cache(g.user['id'], 'dashboard')
        except Exception as e:
            print(f"[AI Welcome] Cache refresh failed: {e}")

    if success: return jsonify({"status": "success", "msg": msg, "data": data})
    return jsonify({"status": "error", "msg": msg, "filename": data}), 500


@bp.route('/run_grading_logic/<int:class_id>', methods=['POST'])
def run_batch_grading(class_id):
    """
    批量批改逻辑 - 并行优化版
    使用线程池并发处理学生作业，并发数由 ThreadPoolExecutor 控制（设为 8），
    实际 AI 请求并发数由 ai_concurrency_manager 根据数据库配置动态控制。
    """
    students = db.get_students_with_grades(class_id)

    # 清空旧成绩
    db.clear_grades(class_id)

    total_students = len(students)
    print(f"[BatchGrading] 开始批改 {total_students} 名学生 (ClassID: {class_id})")

    # 并发执行
    # max_workers 设置为 8，可以允许一定的文件 IO 并发，
    # 而 AI 调用的并发上限会被 ai_concurrency_manager 里的 Semaphore 自动限制（例如 3）
    success_count = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        # 提交所有任务
        future_to_student = {
            executor.submit(GradingService.grade_single_student, class_id, s['student_id']): s
            for s in students
        }

        # 等待完成
        for future in as_completed(future_to_student):
            student = future_to_student[future]
            try:
                success, msg, _ = future.result()
                if success:
                    success_count += 1
                    print(f"[BatchGrading] 学生 {student['name']} ({student['student_id']}) 批改完成")
                else:
                    print(f"[BatchGrading] 学生 {student['name']} 批改失败: {msg}")
            except Exception as exc:
                print(f"[BatchGrading] 学生 {student['name']} 处理异常: {exc}")

    print(f"[BatchGrading] 批改结束. 成功: {success_count}/{total_students}")

    # === 生成成绩文档到文档库 ===
    try:
        # 注意：生成文档是在主线程进行的，不受影响
        from services.score_document_service import ScoreDocumentService
        result = ScoreDocumentService.generate_from_class(class_id, g.user['id'])
        if result:
            print(f"[ScoreDoc] Generated: {result['filename']}")
    except Exception as e:
        import logging
        logging.error(f"[ScoreDoc] Generation failed: {e}")
    # === END ===

    return jsonify({"msg": f"批量批改完成，成功 {success_count}/{total_students} 人"})


@bp.route('/upload_zips/<int:class_id>', methods=['POST'])
def upload_zips(class_id):
    ws_path = FileService.get_real_workspace_path(class_id)
    raw_dir = os.path.join(ws_path, 'raw_zips')
    os.makedirs(raw_dir, exist_ok=True)

    files = request.files.getlist('files')
    count = 0
    uploaded_files = []
    for file in files:
        if file and file.filename:
            file.save(os.path.join(raw_dir, file.filename))
            uploaded_files.append(file.filename)
            count += 1

    # 匹配学生文件
    students = db.get_students_with_grades(class_id)
    matched_students = []

    all_files = os.listdir(raw_dir) if os.path.exists(raw_dir) else []
    for s in students:
        student_id = s['student_id']
        name = s['name']
        matched_file = None
        for f in all_files:
            if str(student_id) in f or name in f:
                matched_file = f
                break
        if matched_file:
            matched_students.append({
                'student_id': student_id,
                'name': name,
                'filename': matched_file
            })

    return jsonify({
        "msg": f"上传 {count} 个文件成功",
        "count": count,
        "matched_count": len(matched_students),
        "total_students": len(students),
        "matched_students": matched_students
    })


@bp.route('/api/file_matches/<int:class_id>')
def api_file_matches(class_id):
    """获取班级学生的文件匹配状态"""
    cls = db.get_class_by_id(class_id)
    if not cls or cls['created_by'] != g.user['id']:
        return jsonify({"msg": "Unauthorized"}), 403

    ws_path = FileService.get_real_workspace_path(class_id)
    raw_dir = os.path.join(ws_path, 'raw_zips')

    students = db.get_students_with_grades(class_id)
    matched_students = []
    total_files = 0

    if os.path.exists(raw_dir):
        all_files = os.listdir(raw_dir)
        total_files = len(all_files)
        for s in students:
            student_id = s['student_id']
            name = s['name']
            matched_file = None
            for f in all_files:
                if str(student_id) in f or name in f:
                    matched_file = f
                    break
            if matched_file:
                matched_students.append({
                    'student_id': student_id,
                    'name': name,
                    'filename': matched_file
                })

    return jsonify({
        "count": total_files,
        "matched_count": len(matched_students),
        "total_students": len(students),
        "matched_students": matched_students
    })


# === 删除了这里重复的 student_detail 和 preview_file 的旧代码 ===


@bp.route('/grading/<int:class_id>/student/<string:student_id>')
def student_detail(class_id, student_id):
    """【补全】学生作业详情页"""
    cls = db.get_class_by_id(class_id)
    student = db.get_student_detail(class_id, student_id)
    if not student: return "Student not found", 404

    # 构建文件树
    ws = FileService.get_real_workspace_path(class_id)
    extract_path = os.path.join(ws, 'extracted', str(student_id))

    def get_file_tree(root_path):
        tree = []
        try:
            items = sorted(os.listdir(root_path))
            for item in items:
                full_path = os.path.join(root_path, item)
                node = {'name': item, 'type': 'folder' if os.path.isdir(full_path) else 'file'}
                if node['type'] == 'folder':
                    node['children'] = get_file_tree(full_path)
                else:
                    node['size'] = os.path.getsize(full_path)
                tree.append(node)
        except Exception:
            pass
        return tree

    file_tree = get_file_tree(extract_path) if os.path.exists(extract_path) else []

    zip_info = {"name": "未提交", "size": 0}
    if student['filename']:
        zip_path = os.path.join(ws, 'raw_zips', student['filename'])
        if os.path.exists(zip_path):
            zip_info = {"name": student['filename'], "size": round(os.path.getsize(zip_path) / 1024, 2)}

    return render_template('student_detail.html', cls=cls, s=student, zip_info=zip_info, file_tree=file_tree,
                           user=g.user)


@bp.route('/preview_file/<int:class_id>/<string:student_id>')
def preview_file(class_id, student_id):
    """【补全】文件预览接口"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    rel_path = request.args.get('path', '')
    if not rel_path: return jsonify({"msg": "Path required"}), 400

    ws_path = FileService.get_real_workspace_path(class_id)
    base_dir = os.path.join(ws_path, 'extracted', str(student_id))

    # 安全路径检查
    full_path = os.path.normpath(os.path.join(base_dir, rel_path))
    if not full_path.startswith(os.path.abspath(base_dir)):
        return jsonify({"msg": "Illegal path access"}), 403

    if not os.path.exists(full_path): return jsonify({"msg": "File not found"}), 404
    if os.path.isdir(full_path): return jsonify({"msg": "Cannot preview directory"}), 400

    # 图片处理
    mime_type, _ = mimetypes.guess_type(full_path)
    if mime_type and mime_type.startswith('image'):
        return send_file(full_path, mimetype=mime_type)

    # 文本处理
    try:
        content = ""
        for enc in ['utf-8', 'gbk', 'gb18030', 'latin1']:
            try:
                with open(full_path, 'r', encoding=enc) as f:
                    content = f.read()
                break
            except:
                continue

        if content:
            if '\0' in content: return jsonify({"type": "binary", "msg": "Binary file"})
            return jsonify({"type": "text", "content": content, "size": os.path.getsize(full_path)})
        else:
            return jsonify({"type": "binary", "msg": "Decode failed"})
    except Exception as e:
        return jsonify({"type": "error", "msg": str(e)}), 500


@bp.route('/export/<int:class_id>')
def export_excel(class_id):
    """
    导出班级成绩为 Excel 文件

    改进：使用智能文件名生成，支持完整的元数据
    支持通过 URL 参数 use_ai=1 启用 AI 文件名生成
    """
    import uuid

    # 检查是否使用 AI 生成文件名
    use_ai = request.args.get('use_ai', '0') == '1'

    # 确保 import json (已在头部添加)
    with db.get_connection() as conn:
        students_data = conn.execute('''
                                     SELECT s.student_id,
                                            s.name,
                                            g.total_score,
                                            g.score_details,
                                            g.deduct_details,
                                            g.filename
                                     FROM students s
                                              LEFT JOIN grades g ON s.student_id = g.student_id AND g.class_id = s.class_id
                                     WHERE s.class_id = ?
                                     ''', (class_id,)).fetchall()
        cls = db.get_class_by_id(class_id)

    if not cls:
        return "班级不存在", 404

    data_list = []
    for row in students_data:
        item = {
            "学号": row['student_id'],
            "姓名": row['name'],
            "总分": row['total_score'] if row['total_score'] is not None else 0,
            "扣分详情": row['deduct_details'],
            "文件名": row['filename']
        }
        if row['score_details']:
            try:
                details = json.loads(row['score_details'])
                for d in details:
                    col_name = d.get('name', '未知项')
                    item[col_name] = d.get('score', 0)
            except:
                pass
        data_list.append(item)

    # 构建 DataFrame
    df = pd.DataFrame(data_list)
    fixed_cols = ['学号', '姓名']
    end_cols = ['总分', '扣分详情', '文件名']
    dynamic_cols = [c for c in df.columns if c not in fixed_cols and c not in end_cols]
    final_cols = fixed_cols + dynamic_cols + end_cols
    df = df[final_cols]

    # === [改进] 智能文件名生成 ===
    # 使用新的文件名生成工具，支持完整的元数据和 AI 生成

    # [调试] 打印班级信息，确认字段正确传递
    print(f"[Export Excel] class_info keys: {list(cls.keys()) if cls else 'None'}")
    if cls:
        print(f"[Export Excel] class_info[name]: {cls.get('name')}")
        print(f"[Export Excel] class_info[course]: {cls.get('course')}")

    local_filename, download_filename = get_export_filename(
        class_info=cls,
        file_type='xlsx',
        use_ai=use_ai,  # 根据 URL 参数决定是否使用 AI
        doc_type='score_sheet'
    )

    # [调试] 打印生成的文件名
    print(f"[Export Excel] Generated download_filename: {download_filename}")
    print(f"[Export Excel] Generated local_filename: {local_filename}")

    # 生成本地保存路径（使用 UUID 避免冲突）
    save_filename = f"export_{class_id}_{uuid.uuid4().hex[:8]}.xlsx"
    save_path = os.path.join(Config.UPLOAD_FOLDER, save_filename)

    print(f"[Export Excel] save_path: {save_path}")
    print(f"[Export Excel] send_file download_name: {download_filename}")

    # 保存 Excel 文件
    df.to_excel(save_path, index=False)

    # 返回文件（自动处理 Excel MIME type）
    return send_file(
        save_path,
        as_attachment=True,
        download_name=download_filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@bp.route('/export/<int:class_id>/ai_filename')
def export_excel_with_ai(class_id):
    """
    导出班级成绩为 Excel 文件（使用 AI 生成文件名）

    这个端点专门用于需要 AI 生成文件名的场景
    返回前会先调用 AI 生成文件名，用户需要稍等片刻
    """
    return export_excel(class_id)


@bp.route('/api/export_to_library/<int:class_id>', methods=['POST'])
def export_to_library(class_id):
    """导出成绩到文档库（Markdown格式）"""
    cls = db.get_class_by_id(class_id)
    if not cls or cls['created_by'] != g.user['id']:
        return jsonify({"status": "error", "msg": "无权限访问"}), 403

    try:
        result = ScoreDocumentService.generate_from_class(class_id, g.user['id'])
        if result:
            return jsonify({
                "status": "success",
                "msg": "成绩已导出到文档库",
                "asset_id": result['asset_id'],
                "filename": result['filename']
            })
        else:
            return jsonify({"status": "error", "msg": "暂无成绩数据可导出"})
    except Exception as e:
        return jsonify({"status": "error", "msg": f"导出失败: {str(e)}"})


def _robust_rmtree(path, max_retries=3):
    """
    Windows 兼容的目录删除函数
    处理文件锁定、只读属性等问题
    """
    import shutil
    import stat
    import time

    def onerror(func, path, exc_info):
        """错误处理：清除只读属性后重试"""
        try:
            os.chmod(path, stat.S_IWUSR | stat.S_IRUSR)
            func(path)
        except Exception:
            pass  # 忽略，让重试机制处理

    for attempt in range(max_retries):
        try:
            if os.path.exists(path):
                shutil.rmtree(path, onerror=onerror)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)  # 等待文件释放
            else:
                # 最后一次尝试：逐个删除文件
                try:
                    for root, dirs, files in os.walk(path, topdown=False):
                        for name in files:
                            file_path = os.path.join(root, name)
                            try:
                                os.chmod(file_path, stat.S_IWUSR | stat.S_IRUSR)
                                os.remove(file_path)
                            except Exception:
                                pass
                        for name in dirs:
                            dir_path = os.path.join(root, name)
                            try:
                                os.rmdir(dir_path)
                            except Exception:
                                pass
                    os.rmdir(path)
                    return True
                except Exception:
                    raise e
    return False


@bp.route('/clear_data/<int:class_id>', methods=['POST'])
def clear_data(class_id):
    """清空班级的所有成绩和上传的文件"""
    cls = db.get_class_by_id(class_id)
    if not cls or cls['created_by'] != g.user['id']:
        return jsonify({"msg": "Unauthorized"}), 403

    # 清空成绩数据
    db.clear_grades(class_id)

    # 删除上传的文件和解压的文件
    ws_path = FileService.get_real_workspace_path(class_id)
    if os.path.exists(ws_path):
        try:
            _robust_rmtree(ws_path)
            os.makedirs(ws_path, exist_ok=True)  # 重建目录
        except Exception as e:
            return jsonify({"msg": f"文件删除失败: {str(e)}"}), 500

    return jsonify({"msg": "成绩和文件已清空\n\n注意：再次批改需要重新上传文件"})


@bp.route('/delete_class/<int:class_id>', methods=['POST'])
def delete_class(class_id):
    """删除班级及其所有相关数据"""
    cls = db.get_class_by_id(class_id)
    if not cls or cls['created_by'] != g.user['id']:
        return jsonify({"msg": "Unauthorized"}), 403

    # 删除数据库记录
    db.delete_class(class_id)

    # 删除工作空间文件
    ws_path = FileService.get_real_workspace_path(class_id)
    if os.path.exists(ws_path):
        try:
            _robust_rmtree(ws_path)
        except Exception as e:
            return jsonify({"msg": f"文件删除失败: {str(e)}"}), 500

    return jsonify({"msg": "班级已删除"})


@bp.route('/api/classes')
def api_classes():
    """获取当前用户的班级列表"""
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401
    classes = db.get_classes(g.user['id'])
    return jsonify(classes)


@bp.route('/api/grading/student_lists', methods=['GET'])
def api_search_student_lists():
    """
    新建班级时的学生名单搜索接口
    权限策略: 允许普通用户查看和选择所有人的名单 (fetch_all=True)
    """
    if not g.user:
        return jsonify([]), 401

    search_query = request.args.get('search', '').strip()

    # 调用 DB 新增的搜索能力，fetch_all=True 确保能看到所有人的数据
    lists = db.get_student_lists(fetch_all=True, search=search_query)

    return jsonify(lists)
