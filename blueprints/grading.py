import mimetypes
import os
import json

import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file, g

from config import Config
from extensions import db
from grading_core.factory import GraderFactory
from services.file_service import FileService
from services.grading_service import GradingService

bp = Blueprint('grading', __name__)


@bp.route('/new_class', methods=['GET', 'POST'])
def new_class():
    if request.method == 'POST':
        cname = request.form['class_name']
        course = request.form['course_name']
        strategy = request.form.get('strategy', '')
        file = request.files['student_list']

        if file:
            cid = db.create_class(cname, course, strategy, g.user['id'])
            # 创建目录
            FileService.get_real_workspace_path(cid)  # 确保目录存在
            db.update_class_workspace(cid, FileService.get_real_workspace_path(cid))

            try:
                df = pd.read_excel(file) if file.filename.endswith('.xlsx') else pd.read_csv(file)
                df.columns = [c.strip() for c in df.columns]
                sid_col = next((c for c in df.columns if '学号' in c), None)
                name_col = next((c for c in df.columns if '姓名' in c), None)
                if sid_col and name_col:
                    for _, row in df.iterrows():
                        db.add_student(str(row[sid_col]), str(row[name_col]), cid)
            except Exception as e:
                return f"名单解析失败: {e}", 400
            return redirect(url_for('grading.grading_view', class_id=cid))

    GraderFactory.load_graders()
    strategies = GraderFactory.get_all_strategies()
    return render_template('newClass.html', strategies=strategies, user=g.user)


@bp.route('/grading/<int:class_id>')
def grading_view(class_id):
    cls = db.get_class_by_id(class_id)
    if not cls or cls['created_by'] != g.user['id']: return "Unauthorized", 403
    students = db.get_students_with_grades(class_id)
    return render_template('grading.html', cls=cls, students=students, user=g.user)


@bp.route('/api/grade_student/<int:class_id>/<string:student_id>', methods=['POST'])
def api_grade_student(class_id, student_id):
    success, msg, data = GradingService.grade_single_student(class_id, student_id)
    if success: return jsonify({"status": "success", "msg": msg, "data": data})
    return jsonify({"status": "error", "msg": msg, "filename": data}), 500


@bp.route('/run_grading_logic/<int:class_id>', methods=['POST'])
def run_batch_grading(class_id):
    # 批量批改逻辑，循环调用 Service
    students = db.get_students_with_grades(class_id)
    db.clear_grades(class_id)
    for s in students:
        GradingService.grade_single_student(class_id, s['student_id'])
    return jsonify({"msg": "批量批改完成"})


@bp.route('/upload_zips/<int:class_id>', methods=['POST'])
def upload_zips(class_id):
    ws_path = FileService.get_real_workspace_path(class_id)
    raw_dir = os.path.join(ws_path, 'raw_zips')
    os.makedirs(raw_dir, exist_ok=True)

    files = request.files.getlist('files')
    count = 0
    for file in files:
        if file and file.filename:
            file.save(os.path.join(raw_dir, file.filename))
            count += 1
    return jsonify({"msg": f"上传 {count} 个文件成功"})


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

    df = pd.DataFrame(data_list)
    fixed_cols = ['学号', '姓名']
    end_cols = ['总分', '扣分详情', '文件名']
    dynamic_cols = [c for c in df.columns if c not in fixed_cols and c not in end_cols]
    final_cols = fixed_cols + dynamic_cols + end_cols
    df = df[final_cols]

    path = os.path.join(Config.UPLOAD_FOLDER, f"{cls['name']}_成绩单.xlsx")
    df.to_excel(path, index=False)
    return send_file(path, as_attachment=True)


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
    import shutil
    if os.path.exists(ws_path):
        try:
            shutil.rmtree(ws_path)
            os.makedirs(ws_path, exist_ok=True)  # 重建目录
        except Exception as e:
            return jsonify({"msg": f"文件删除失败: {str(e)}"}), 500

    return jsonify({"msg": "成绩和文件已清空"})


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
    import shutil
    if os.path.exists(ws_path):
        try:
            shutil.rmtree(ws_path)
        except Exception as e:
            return jsonify({"msg": f"文件删除失败: {str(e)}"}), 500

    return jsonify({"msg": "班级已删除"})
