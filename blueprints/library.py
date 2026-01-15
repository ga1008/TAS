import asyncio
import base64
import json
import mimetypes
import os
import traceback

import httpx
from flask import Blueprint, render_template, request, jsonify, g, current_app

from ai_utils.ai_helper import call_ai_platform_chat
from export_core.doc_config import DocumentTypeConfig
from extensions import db
from services.ai_service import AiService
from services.file_service import FileService
from utils.common import calculate_file_hash, generate_title_from_content, create_text_asset, extract_title_and_content

bp = Blueprint('library', __name__)


@bp.route('/library/view')
def index():
    """文档库视图"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401
    return render_template('library/index.html', user=g.user)


@bp.route('/file_manager')
def file_manager_page():
    """【补全】旧版文件管理器页面"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401
    return render_template('file_manager.html', user=g.user)


# === 列表与筛选 API ===

@bp.route('/api/library/files')
def api_library_files():
    """文档库高级筛选接口"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    category = request.args.get('category', '')
    year = request.args.get('year', '')
    course = request.args.get('course', '')
    search = request.args.get('q', '')

    files = db.get_files_by_filter(
        user_id=g.user['id'],
        doc_category=category if category != 'all' else None,
        year=year,
        course=course,
        search=search  # 假设 DB 层已支持，或在下方过滤
    )

    # 补全权限标记
    for f in files:
        f['is_owner'] = (f['uploaded_by'] == g.user['id']) or g.user.get('is_admin')

    return jsonify(files)


@bp.route('/api/library/filters')
def api_library_filters():
    """左侧筛选树"""
    if not g.user: return jsonify([]), 401
    tree = db.get_document_library_tree(g.user['id'])
    return jsonify(tree)


@bp.route('/api/my_files')
def my_files():
    """【补全】获取当前用户最近文件"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401
    search = request.args.get('q', '')
    files = db.get_user_recent_files(g.user['id'], limit=50, search_name=search)
    return jsonify(files)


@bp.route('/api/files')
def all_files():
    """【补全】获取所有文件（用于公共选择）"""
    search = request.args.get('q', '')
    files = db.get_files(limit=50, search_name=search)
    return jsonify(files)


@bp.route('/api/my_parsed_files')
def my_parsed_files():
    """【补全】获取已解析的文件"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401
    files = db.get_user_parsed_files(g.user['id'])
    for f in files:
        f['is_owner'] = f.get('uploaded_by') == g.user['id']
    return jsonify(files)


# === 文件操作 API ===

@bp.route('/api/parse_file_asset', methods=['POST'])
def parse_file_asset():
    """上传并解析文件"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    f = request.files.get('file')
    if not f: return jsonify({"msg": "请先选择文件"}), 400

    try:
        # 1. 保存/查重
        path, _ = FileService.handle_file_upload_or_reuse(f, None, g.user['id'])
        if not path: return jsonify({"msg": "文件保存失败"}), 400

        # 2. 获取记录
        with open(path, 'rb') as f_stream:
            f_hash = calculate_file_hash(f_stream)
        record = db.get_file_by_hash(f_hash)

        # 3. 智能解析
        doc_type = request.form.get('doc_type')
        success, content, meta = AiService.smart_parse_content(record['id'], doc_type)

        if not success: return jsonify({"msg": content}), 400

        return jsonify({
            "status": "success",
            "file_id": record['id'],
            "title": record['original_name'],
            "parsed_content": content
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"msg": f"解析失败: {str(e)}"}), 500


@bp.route('/api/save_pasted_document', methods=['POST'])
def save_pasted_document():
    """【补全】保存粘贴的文本"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    data = request.json or {}
    content = (data.get('content') or '').strip()
    doc_type = data.get('doc_type')

    if not content: return jsonify({"msg": "内容不能为空"}), 400

    # 生成标题并保存
    # 注意：这里调用 FileService 的辅助方法，如果没封装，可以用 AiService 生成标题
    title = FileService.generate_title_from_content(content, doc_type)
    file_id, filename = FileService.create_text_asset(content, title, g.user['id'])

    if not file_id: return jsonify({"msg": "保存失败"}), 500

    return jsonify({"status": "success", "file_id": file_id, "title": filename})


@bp.route('/api/parse_and_save_pasted_document', methods=['POST'])
def parse_and_save_pasted_document():
    """
    粘贴入库：先让 AI 整理成 JSON 结构，然后后端拆包存库。
    解决：之前存入的是 raw json 导致的格式错误问题。
    """
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.json or {}
    content = (data.get('content') or '').strip()
    doc_type = data.get('doc_type')

    if not content:
        return jsonify({"msg": "内容不能为空"}), 400

    doc_label = "试卷" if doc_type == "exam" else "评分标准"
    standard_config = db.get_best_ai_config("standard") or db.get_best_ai_config("thinking")

    if not standard_config:
        # 如果没有 AI 配置，直接保存原始内容
        title = generate_title_from_content(content, doc_type)
        file_id, filename = create_text_asset(content, title, g.user['id'])
        return jsonify({"status": "success", "file_id": file_id, "title": filename, "msg": "未配置AI，已原样保存"})

    # Prompt 要求返回 JSON，以便分离标题和正文
    prompt = (
        f"请对以下{doc_label}内容进行深度规整。\n"
        "1. 去除无用的页眉页脚、乱码。\n"
        "2. 将内容整理为清晰的 Standard Markdown 格式。\n"
        "3. 根据文档类型和内容为文档起一个合理的标题。\n"
        "4. **必须以纯 JSON 格式返回**，不要使用代码块标记，格式如下：\n"
        "{\"title\": \"文档标题\", \"content\": \"Markdown格式的正文内容...\"}\n\n"
        f"原始内容：\n{content}"
    )

    try:
        ai_text = asyncio.run(call_ai_platform_chat(
            system_prompt="你是文档整理助手。你只输出 JSON。",
            messages=[{"role": "user", "content": prompt}],
            platform_config=standard_config
        ))

        # 使用增强版工具函数提取
        title, normalized_content = extract_title_and_content(ai_text, doc_type)

        if not normalized_content:
            return jsonify({"msg": "AI 解析内容为空"}), 500

        # === 核心修正：这里存入的是 normalized_content (Markdown)，而不是 ai_text (JSON) ===
        file_id, filename = create_text_asset(normalized_content, title, g.user['id'])

        if not file_id:
            return jsonify({"msg": "保存失败"}), 500

        return jsonify({"status": "success", "file_id": file_id, "title": filename})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"msg": f"解析保存失败: {str(e)}"}), 500


@bp.route('/api/update_file_content', methods=['POST'])
def update_file_content():
    """【补全】更新文件内容（在线编辑）"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    data = request.json or {}
    file_id = data.get('id')
    content = data.get('content')

    if not file_id or content is None: return jsonify({"msg": "参数错误"}), 400

    record = db.get_file_by_id(file_id)
    if not record: return jsonify({"msg": "文件不存在"}), 404

    # 权限检查
    if int(record['uploaded_by']) != int(g.user['id']) and not g.user.get('is_admin'):
        return jsonify({"msg": "无权编辑他人文档"}), 403

    db.update_file_parsed_content(file_id, content)
    return jsonify({"status": "success", "msg": "保存成功"})


@bp.route('/api/delete_file_asset', methods=['POST'])
def delete_file_asset():
    """【补全】删除文件"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    file_id = request.json.get('id')
    file_record = db.get_file_by_id(file_id)
    if not file_record: return jsonify({"msg": "文件不存在"}), 404

    if int(file_record['uploaded_by']) != int(g.user['id']) and not g.user.get('is_admin'):
        return jsonify({"msg": "无权删除此文件"}), 403

    db.delete_file_asset(file_id)
    # 尝试删除物理文件
    try:
        if os.path.exists(file_record['physical_path']):
            os.remove(file_record['physical_path'])
    except:
        pass
    return jsonify({"msg": "删除成功"})


@bp.route('/api/ai_generate_document', methods=['POST'])
def ai_generate_document():
    """【补全】AI 生成文档（支持图片上传）"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    prompt = (request.form.get('prompt') or '').strip()
    doc_type = request.form.get('doc_type') or 'exam'

    uploaded_files = request.files.getlist('files')
    existing_file_ids = request.form.getlist('existing_file_ids')

    if not prompt and not uploaded_files and not existing_file_ids:
        return jsonify({"msg": "请输入提示词或提供参考素材"}), 400

    # 逻辑迁移：调用 AiService 处理复杂生成任务
    # 为了不让 Controller 过于臃肿，这部分逻辑建议封装到 Service
    # 但为了确保功能完全一致，这里保留关键流程

    try:
        image_payloads = []
        doc_texts = []

        # A. 处理上传
        for f in uploaded_files:
            if not f or not f.filename: continue
            path, name = FileService.handle_file_upload_or_reuse(f, None, g.user['id'])
            if not path: continue

            ext = os.path.splitext(path)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.webp']:
                with open(path, 'rb') as img_f:
                    b64 = base64.b64encode(img_f.read()).decode('utf-8')
                mime = mimetypes.types_map.get(ext, 'image/png')
                image_payloads.append({"type": "image", "data": f"data:{mime};base64,{b64}"})
            else:
                ok, text = FileService.extract_text_from_file(path)
                if ok: doc_texts.append({"name": name, "content": text})

        # B. 处理引用
        for eid in existing_file_ids:
            rec = db.get_file_by_id(eid)
            if rec and rec.get('parsed_content'):
                doc_texts.append({"name": f"[库]{rec['original_name']}", "content": rec['parsed_content']})

        # C. 组装 Prompt
        sys_prompt = DocumentTypeConfig.get_prompt_by_type(doc_type)
        user_msg = [f"【生成任务】\n请生成一份【{DocumentTypeConfig.TYPES.get(doc_type, '文档')}】。", f"要求：{prompt}"]

        if doc_texts:
            user_msg.append("\n【参考素材】：")
            for d in doc_texts:
                user_msg.append(f"--- {d['name']} ---\n{d['content'][:30000]}\n")

        user_msg.append("\n请严格遵循 JSON 输出格式 {metadata:..., content:...}")

        # D. 调用 AI
        config_type = "vision" if image_payloads else "thinking"  # 优先 thinking
        best_conf = db.get_best_ai_config(config_type) or db.get_best_ai_config("standard")

        if not best_conf: return jsonify({"msg": "未配置 AI 模型"}), 500

        payload = {
            "system_prompt": sys_prompt,
            "messages": [],
            "new_message": "\n".join(user_msg),
            "model_capability": "vision" if image_payloads else best_conf['provider_type']  # 这里的逻辑根据实际 provider 调整
        }

        if image_payloads:
            payload["messages"].append({"role": "user", "content": "参考图", "file_ids": image_payloads})
            payload["model_capability"] = "vision"

        # 发送请求 (复用 ai_helper 或者 requests)
        # 这里假设 extensions 或 ai_helper 能直接用，或者直接 requests
        endpoint = current_app.config['AI_ASSISTANT_CHAT_ENDPOINT']
        resp = httpx.post(endpoint, json=payload, timeout=240.0)

        if resp.status_code != 200:
            return jsonify({"msg": f"AI Error: {resp.text}"}), 500

        ai_text = resp.json().get("response_text", "")

        # E. 解析与保存
        success, content, meta = AiService._process_ai_json_response(ai_text, None, doc_type)  # 复用 Service 内部解析方法

        # 尝试生成标题
        title = meta.get("course_name", "") + " " + DocumentTypeConfig.TYPES.get(doc_type, "文档")
        if len(title) < 5: title = FileService.generate_title_from_content(content, doc_type)

        file_id, filename = FileService.create_text_asset(content, title, g.user['id'])

        # 更新 Meta
        if file_id and meta:
            conn = db.get_connection()
            conn.execute("UPDATE file_assets SET meta_info=? WHERE id=?",
                         (json.dumps(meta, ensure_ascii=False), file_id))
            conn.commit()

        return jsonify({"status": "success", "file_id": file_id, "title": filename})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"msg": f"生成失败: {str(e)}"}), 500
