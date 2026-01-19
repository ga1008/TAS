import os
import shutil
import threading
import time
import uuid

from flask import Blueprint, render_template, request, jsonify, g, current_app

from config import Config
from extensions import db
from grading_core.direct_grader_template import DIRECT_GRADER_TEMPLATE
from grading_core.factory import GraderFactory
from services.ai_service import AiService
from services.file_service import FileService
from utils.common import calculate_file_hash

bp = Blueprint('ai_gen', __name__)


@bp.route('/ai_generator')
def ai_generator_page():
    ref_task_id = request.args.get('ref_task_id')
    ref_task = None
    if ref_task_id:
        ref_task = db.get_ai_task_by_id(ref_task_id)

    GraderFactory.load_graders()
    strategies = GraderFactory.get_all_strategies()
    display_list = []

    active_ids = set()
    for sid, sname, course in strategies:
        active_ids.add(sid)
        task = db.get_task_by_grader_id(sid)
        # 只有 Admin 或者 创建者本人 才是 is_owner
        is_owner = False
        if task and task.get('creator_id') == g.user['id']:
            is_owner = True

        creator_name = task.get('creator_name', 'System') if task else 'Built-in'
        info = {
            "type": "grader",
            "id": sid,
            "name": sname,
            "status": "success",
            "log_info": "Ready",
            "created_at": task['created_at'] if task else "未知",
            "source": "AI 生成" if task else "系统内置",
            "creator": creator_name,
            "is_owner": is_owner
        }
        display_list.append(info)

    recent_tasks = db.get_ai_tasks(limit=50)

    for t in recent_tasks:
        if t['status'] == 'deleted':
            continue

        is_owner = (t.get('created_by') == g.user['id'])

        # === 【修改点 1】: 过滤他人的失败/进行中任务，保持列表干净 ===
        # 如果任务失败，且不是我创建的，则不显示
        if t['status'] == 'failed' and not is_owner:
            continue

        if t['status'] in ['pending', 'processing', 'failed']:
            display_list.append({
                "type": "task",
                "id": t['id'],
                "task_name": t['name'],
                "status": t['status'],
                "log_info": t['log_info'],
                "created_at": t['created_at'],
                "source": "正在生成..." if t['status'] != 'failed' else "生成失败",
                "creator": t.get('creator_name', 'Unknown'),
                "is_owner": is_owner,
                "grader_id": t.get('grader_id')  # 确保传递 grader_id 以便删除
            })
        elif t['status'] == 'success' and t['grader_id'] and t['grader_id'] not in active_ids:
            # 数据库显示成功，但内存没加载到，提示刷新
            expected_path = os.path.join(Config.GRADERS_DIR, f"{t['grader_id']}.py")
            if os.path.exists(expected_path):
                display_list.append({
                    "type": "grader",
                    "id": t['grader_id'],
                    "name": t['name'] + " (需刷新)",
                    "status": "success",
                    "log_info": "已就绪",
                    "created_at": t['created_at'],
                    "source": "AI 生成",
                    "creator": t.get('creator_name', 'Unknown'),
                    "is_owner": is_owner
                })
            else:
                # 文件彻底丢了，标为 deleted
                db.update_task_status_by_grader_id(t['grader_id'], "deleted")
                continue

    display_list.sort(key=lambda x: x['created_at'], reverse=True)

    return render_template('ai_generator.html', ref_task=ref_task, graders=display_list, user=g.user)


@bp.route('/api/create_grader_task', methods=['POST'])
def create_task():
    name = request.form.get('task_name')
    strictness = request.form.get('strictness', 'standard')
    extra_desc = request.form.get('extra_desc', '')
    max_score = int(request.form.get('max_score', 100))

    f_exam = request.files.get('exam_file')
    f_std = request.files.get('standard_file')

    course_name = request.files.get('course_name')

    # 使用 FileService 处理上传
    exam_path, _ = FileService.handle_file_upload_or_reuse(f_exam, request.form.get('exam_file_id'), g.user['id'])
    std_path, _ = FileService.handle_file_upload_or_reuse(f_std, request.form.get('standard_file_id'), g.user['id'])

    if not exam_path or not std_path: return jsonify({"msg": "文件缺失"}), 400

    # 提取文本
    _, exam_text = FileService.extract_text_from_file(exam_path)
    _, std_text = FileService.extract_text_from_file(std_path)

    task_id = db.insert_ai_task(name, "pending", "提交中...", exam_path, std_path, strictness, extra_desc, max_score,
                                g.user['id'], course_name)

    # 启动线程
    app_config = current_app.config  # 传递 config 给线程
    t = threading.Thread(target=AiService.generate_grader_worker,
                         args=(task_id, exam_text, std_text, strictness, extra_desc, max_score, app_config, course_name))
    t.start()

    return jsonify({"msg": "任务已提交", "task_id": task_id})


@bp.route('/grader/<string:grader_id>')
def grader_detail(grader_id):
    GraderFactory.load_graders()
    grader_cls = GraderFactory._graders.get(grader_id)
    task_info = db.get_task_by_grader_id(grader_id)
    file_path = os.path.join(Config.GRADERS_DIR, f"{grader_id}.py")
    code_content = ""
    file_exists = os.path.exists(file_path)

    if file_exists:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
        except:
            code_content = "# 读取文件失败"

    if not grader_cls and not task_info and not file_exists:
        return "核心未找到或已被删除", 404

    if grader_cls:
        display_name = grader_cls.NAME
        status_tag = "normal"
    else:
        base_name = task_info.get('name', grader_id) if task_info else grader_id
        display_name = f"{base_name} (⚠ 加载失败-请检查代码)"
        status_tag = "error"

    is_owner = False
    if task_info and g.user and task_info.get('creator_id') == g.user['id']:
        is_owner = True
    if not task_info and g.user and g.user.get('is_admin'):
        is_owner = True

    return render_template('grader_detail.html',
                           grader={"id": grader_id, "name": display_name, "code": code_content, "status": status_tag},
                           task=task_info, is_owner=is_owner, user=g.user)


@bp.route('/api/delete_grader', methods=['POST'])
def delete_grader():
    # 前端可能传过来 grader_id (str) 或者 task_id (int/str)
    raw_id = request.json.get('id')
    if not raw_id:
        return jsonify({"msg": "ID不能为空"}), 400

    task = None

    # 1. 尝试逻辑：先判断是不是 Task ID (数字)
    # 失败的任务通常只剩下 Task ID，没有 grader_id
    if str(raw_id).isdigit():
        task = db.get_ai_task_by_id(int(raw_id))

    # 2. 如果没找到，或者传来的明显是 grader_id (如 "direct_xxxx")
    # 则尝试按 grader_id 查找
    if not task:
        task = db.get_task_by_grader_id(raw_id)

    if not task:
        # 如果既找不到任务，文件也不存在，可能是旧数据遗留
        return jsonify({"msg": "任务记录不存在，无法删除"}), 404

    # 3. 权限检查
    # 必须是创建者或者管理员
    if task.get('created_by') != g.user['id'] and not g.user.get('is_admin'):
        return jsonify({"msg": "您无权删除他人创建的核心"}), 403

    # 4. 执行删除操作

    # A. 物理文件删除 (只有当 grader_id 存在时才需要删文件)
    grader_id = task.get('grader_id')
    if grader_id:
        file_path = os.path.join(Config.GRADERS_DIR, f"{grader_id}.py")
        # 即使文件不存在也不报错，继续删数据库记录
        if os.path.exists(file_path):
            timestamp = int(time.time())
            backup_name = f"{grader_id}_{timestamp}.py.bak"
            backup_path = os.path.join(Config.TRASH_DIR, backup_name)
            try:
                shutil.move(file_path, backup_path)

                # 记录进回收站表
                GraderFactory.load_graders()
                g_cls = GraderFactory._graders.get(grader_id)
                name = g_cls.NAME if g_cls else (task.get('name') or grader_id)
                db.recycle_grader_record(grader_id, name, backup_name)
            except Exception as e:
                print(f"[Delete Error] Move file failed: {e}")

    # B. 数据库状态软删除 (关键修复：使用 Task ID 更新)
    # 这样即使 grader_id 为空，也能成功将状态置为 deleted
    db.update_ai_task_status(task['id'], "deleted")

    # C. 尝试热重载 (移除内存中的对象)
    GraderFactory._loaded = False
    GraderFactory.load_graders()

    return jsonify({"msg": "已移入回收站"})


@bp.route('/api/create_direct_grader', methods=['POST'])
def create_direct_grader():
    """【补全】创建直通模式评分核心"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    name = request.form.get('grader_name')
    extra = request.form.get('extra_instruction', '')

    f_exam = request.files.get('exam_file')
    f_std = request.files.get('standard_file')

    course_name = request.files.get('course_name')

    # 复用 FileService
    exam_path, _ = FileService.handle_file_upload_or_reuse(f_exam, request.form.get('exam_file_id'), g.user['id'])
    std_path, _ = FileService.handle_file_upload_or_reuse(f_std, request.form.get('standard_file_id'), g.user['id'])

    if not exam_path or not std_path: return jsonify({"msg": "文件缺失"}), 400

    # 智能解析
    # 这里需要获取 file_id，可以通过 hash 获取
    with open(exam_path, 'rb') as f:
        ex_rec = db.get_file_by_hash(calculate_file_hash(f))
    with open(std_path, 'rb') as f:
        std_rec = db.get_file_by_hash(calculate_file_hash(f))

    _, p_exam, _ = AiService.smart_parse_content(ex_rec['id'])
    _, p_std, _ = AiService.smart_parse_content(std_rec['id'])

    # 生成代码
    grader_id = f"direct_{uuid.uuid4().hex[:8]}"
    class_name = f"DirectGrader_{grader_id}"

    def safe_str(s):
        if not s: return ""
        return s.replace('\x00', '').replace('\\', '\\\\').replace('"', '\\"').replace("'''", "\\'\\'\\'")

    code = DIRECT_GRADER_TEMPLATE.format(
        class_name=class_name, grader_id=grader_id, display_name=name, course_name=course_name,
        exam_content=safe_str(p_exam), std_content=safe_str(p_std), extra_instruction=safe_str(extra)
    )

    # 保存与注册
    save_path = os.path.join(current_app.config['GRADERS_DIR'], f"{grader_id}.py")
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(code)

    db.insert_ai_task(name, 'success', 'Direct Created', exam_path, std_path, 'direct', '', 0, g.user['id'], grader_id, course_name)
    GraderFactory._loaded = False
    GraderFactory.load_graders()

    return jsonify({"status": "success"})
