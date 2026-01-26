import json
import os
import uuid
from urllib.parse import quote

from flask import Blueprint, request, jsonify, send_file, render_template, g, current_app

from config import Config
from export_core.manager import TemplateManager
from extensions import db
from utils.common import get_corrected_path

bp = Blueprint('export', __name__)


def load_export_templates():
    """加载内置导出模板到数据库"""
    templates_dir = current_app.config['TEMPLATE_DIR']
    TemplateManager.load_templates(templates_dir)


@bp.route('/export_page/<int:file_id>')
def export_page(file_id):
    """渲染导出配置页面"""
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401  # 或者 redirect login
    load_export_templates()
    record = db.get_file_by_id(file_id)
    if not record:
        return "文件不存在", 404

    # 尝试智能提取课程名 (如果原来的标题里有)
    metadata = {"course_name": "", "class_name": ""}
    if record['original_name']:
        metadata['course_name'] = record['original_name'].replace('.txt', '').replace('.md', '')

    return render_template('export.html',
                           file=record,
                           content=record.get('parsed_content', ''),
                           metadata=metadata,
                           user=g.user)


@bp.route('/api/export/templates')
def get_export_templates():
    """获取可用导出模板"""
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    conn = db.get_connection()
    # 假设 export_templates 表存在
    templates = conn.execute(
        "SELECT template_id, name, description, ui_schema FROM export_templates WHERE is_active=1"
    ).fetchall()
    return jsonify([dict(row) for row in templates])


@bp.route('/api/export_word_v2', methods=['POST'])
def export_word_v2():
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    data = request.json
    file_id = data.get('file_id')
    template_id = data.get('template_id')
    form_data = data.get('form_data', {})  # 前端动态表单填写的KV

    # 获取文件内容和元数据
    file_record = db.get_file_by_id(file_id)
    if not file_record:
        return jsonify({"msg": "文件记录不存在"}), 404

    content = file_record['parsed_content']
    meta_info = json.loads(file_record.get('meta_info') or '{}')

    # 获取模板实例
    exporter = TemplateManager.get_template(template_id)
    if not exporter:
        return jsonify({"msg": "模板未找到"}), 404

    # === [FIX 1] 修复字典遍历报错 ===
    # 处理签名路径逻辑 (将 ID 转为 Path)
    # 使用 list() 创建 items 的副本进行遍历，避免 "dictionary changed size" 错误
    for key, val in list(form_data.items()):
        # 只要 key 是 _sig 结尾（如 teacher_sig）或者是特定的 _select 结尾（兼容旧逻辑），且值为数字 ID
        is_sig_field = key.endswith('_sig') or key.endswith('_select')

        if is_sig_field and str(val).isdigit():
            sig = db.get_signature_by_id(int(val))
            if sig:
                # 注入 path 供模板使用
                # 注意：这里我们向 form_data 添加了新 Key，所以外层必须用 list() 拷贝迭代
                real_path = get_corrected_path(sig['file_path'], Config.SIGNATURES_FOLDER)
                if real_path:
                    # 如果 key 是 teacher_sig，则注入 teacher_sig_path
                    # 如果 key 是 teacher_sig_select，则注入 teacher_sig_path (保持兼容)
                    prefix = key.replace('_select', '')
                    form_data[f"{prefix}_path"] = real_path

    # 生成文件
    ext = getattr(exporter, 'FILE_EXTENSION', 'docx')
    filename = f"export_{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(Config.UPLOAD_FOLDER, filename)

    try:
        exporter.generate(content, meta_info, form_data, save_path)

        # === [FIX 2] 补全中文文件名处理 ===
        dl_name = form_data.get('course_name', 'Document')
        # 确保文件名是字符串
        if not dl_name: dl_name = 'Document'

        try:
            # 尝试编码，如果不报错说明是纯 ASCII，不需要 quote
            dl_name.encode('latin-1')
            final_name = f"{dl_name}.{ext}"
        except UnicodeEncodeError:
            # 包含中文，使用 URL 编码防止 header 错误
            final_name = f"{quote(dl_name)}.{ext}"
        # 针对 Excel 修正 MIME type

        mimetype = None
        if ext == 'xlsx':
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

        return send_file(save_path, as_attachment=True, download_name=final_name, mimetype=mimetype)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"msg": f"导出失败: {str(e)}"}), 500


@bp.route('/api/export/score_sheet/<int:asset_id>/config')
def get_score_sheet_export_config(asset_id):
    """
    获取考核登分表的 Excel 导出配置

    返回动态字段配置，用于前端生成表单

    Returns:
        {
            "status": "success",
            "export_config": {
                "auto_fill": {...},  // 自动填充字段
                "question_fields": [{"name": ..., "max_score": ...}, ...],
                "total_score": ...
            }
        }
    """
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    file_record = db.get_file_by_id(asset_id)
    if not file_record:
        return jsonify({"msg": "文档不存在"}), 404

    if file_record.get('doc_category') != 'score_sheet':
        return jsonify({"msg": "该文档不是考核登分表类型"}), 400

    # 解析 meta_info
    meta_info = {}
    if file_record.get('meta_info'):
        try:
            meta_info = json.loads(file_record['meta_info'])
        except (json.JSONDecodeError, TypeError):
            pass

    # 构建导出配置
    question_scores = meta_info.get('question_scores', [])

    export_config = {
        "auto_fill": {
            "course_name": meta_info.get('course_name', ''),
            "course_code": meta_info.get('course_code', ''),
            "class_name": meta_info.get('class_name', ''),
            "teacher": meta_info.get('teacher', ''),
            "academic_year_semester": meta_info.get('academic_year_semester', '')
        },
        "question_fields": [
            {
                "name": q.get('name', f'题目{i+1}'),
                "label": q.get('name', f'第{i+1}题'),
                "max_score": q.get('max_score', 0)
            }
            for i, q in enumerate(question_scores)
        ],
        "total_score": meta_info.get('total_max_score', 100)
    }

    return jsonify({
        "status": "success",
        "export_config": export_config
    })
