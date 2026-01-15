import os

from flask import Blueprint, request, jsonify, send_file, g, current_app

from extensions import db
from utils.common import calculate_file_hash, get_corrected_path

# 定义蓝图，统一前缀 /api/signatures
bp = Blueprint('signatures', __name__, url_prefix='/api/signatures')


@bp.route('/list')
def list_signatures():
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    search = request.args.get('q', '')
    sigs = db.get_signatures(search)

    # 标记 ownership (前端用于判断是否显示删除按钮)
    for s in sigs:
        s['is_owner'] = (s['uploaded_by'] == g.user['id']) or (g.user.get('is_admin'))

    return jsonify(sigs)


@bp.route('/upload', methods=['POST'])
def upload_signature():
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    file = request.files.get('file')
    name = request.form.get('name', '').strip()

    if not file:
        return jsonify({"msg": "请选择文件"}), 400
    if not name:
        name = file.filename

    # 格式校验
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg']:
        return jsonify({"msg": "仅支持 PNG/JPG 格式"}), 400

    # 物理保存 (Hash去重)
    f_hash = calculate_file_hash(file)
    save_name = f"{f_hash}{ext}"

    # 获取配置中的文件夹路径
    signatures_folder = current_app.config['SIGNATURES_FOLDER']
    save_path = os.path.join(signatures_folder, save_name)

    if not os.path.exists(save_path):
        file.save(save_path)

    # 数据库记录
    db.add_signature(name, f_hash, save_path, g.user['id'])
    return jsonify({"status": "success"})


@bp.route('/delete', methods=['POST'])
def delete_signature():
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    sig_id = request.json.get('id')
    sig = db.get_signature_by_id(sig_id)

    if not sig:
        return jsonify({"msg": "记录不存在"}), 404

    # 权限检查：只能删自己的，或者是管理员
    if sig['uploaded_by'] != g.user['id'] and not g.user.get('is_admin'):
        return jsonify({"msg": "无权删除他人上传的签名"}), 403

    # 逻辑删除：先删DB记录
    db.delete_signature(sig_id)

    # [物理清理检查]
    # 检查该物理文件是否还有其他签名记录在使用（基于Hash）
    usage = db.get_signature_usage_count(sig['file_hash'])

    signatures_folder = current_app.config['SIGNATURES_FOLDER']
    real_path = get_corrected_path(sig['file_path'], signatures_folder)

    if usage == 0 and real_path and os.path.exists(real_path):
        try:
            os.remove(real_path)
        except Exception as e:
            print(f"Failed to remove signature file: {e}")

    return jsonify({"status": "success"})


@bp.route('/image/<int:sig_id>')
def get_signature_image(sig_id):
    if not g.user:
        return jsonify({"msg": "Unauthorized"}), 401

    sig = db.get_signature_by_id(sig_id)
    if not sig:
        return "Record not found", 404

    # [路径修复] 核心修复点：获取真实路径 (兼容不同操作系统迁移的数据)
    signatures_folder = current_app.config['SIGNATURES_FOLDER']
    real_path = get_corrected_path(sig['file_path'], signatures_folder)

    if not real_path:
        return "Image file not found on server", 404

    return send_file(real_path)
