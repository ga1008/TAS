# utils/common.py
import hashlib
import json
import os
import re
import time

from config import Config
from export_core.doc_config import DocumentTypeConfig
from extensions import db


def calculate_file_hash(file_stream):
    """计算文件的 SHA256 哈希值"""
    sha256 = hashlib.sha256()
    file_stream.seek(0)
    while chunk := file_stream.read(8192):
        sha256.update(chunk)
    file_stream.seek(0)
    return sha256.hexdigest()


def sanitize_filename(name, fallback="未命名文档"):
    clean = re.sub(r'[\\/*?:"<>|]', '', name or '').strip()
    return clean or fallback


def is_content_garbage(text):
    """检测文本是否为乱码"""
    if not text: return False
    if '\x00' in text: return True  # Null Byte
    total_len = len(text)
    if total_len == 0: return False
    control_chars = [c for c in text if 0 <= ord(c) < 32 and c not in ('\t', '\n', '\r')]
    if total_len > 50 and (len(control_chars) / total_len) > 0.05:
        return True
    if "bjbj" in text and (len(control_chars) / total_len) > 0.01:
        return True
    return False


def get_corrected_path(db_path, folder_path):
    """跨平台路径修复工具"""
    if not db_path: return None
    if os.path.exists(db_path): return db_path
    filename = os.path.basename(db_path.replace('\\', '/'))
    corrected_path = os.path.join(folder_path, filename)
    return corrected_path if os.path.exists(corrected_path) else None


def generate_title_from_content(content, doc_type=None):
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if lines:
        candidate = re.sub(r'^#+\s*', '', lines[0]).strip()
        if candidate:
            return sanitize_filename(candidate[:40])

    prefix = "试卷" if doc_type == "exam" else "评分标准"
    timestamp = time.strftime("%Y%m%d_%H%M")
    return f"{prefix}_{timestamp}"


def create_text_asset(content, title, user_id, ext=".md"):
    encoded = content.encode('utf-8')
    file_hash = hashlib.sha256(encoded).hexdigest()
    safe_title = sanitize_filename(title)
    filename = f"{safe_title}{ext}"
    physical_path = os.path.normpath(os.path.join(Config.FILE_REPO_FOLDER, f"{file_hash}{ext}"))

    if not os.path.exists(physical_path):
        with open(physical_path, 'wb') as f:
            f.write(encoded)

    file_id = db.save_file_asset(file_hash, filename, len(encoded), physical_path, user_id)
    if file_id:
        db.update_file_parsed_content(file_id, content)
    return file_id, filename


def extract_title_and_content(ai_text, doc_type=None):
    """
    解析 AI 返回的 JSON 或 文本。
    返回: (title, content, metadata_dict)
    """
    cleaned = ai_text.strip()
    meta = {}
    content = ""
    title = ""

    # 1. 尝试 Regex 提取 JSON
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(1)

    try:
        # 尝试寻找 JSON 边界
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1:
            potential_json = cleaned[start:end + 1]
            payload = json.loads(potential_json)

            # 兼容新旧格式
            content = payload.get("content") or payload.get("body") or ""
            meta = payload.get("metadata") or {}

            # 尝试从 meta 拼凑标题
            if meta.get("course_name"):
                suffix = DocumentTypeConfig.TYPES.get(doc_type, "文档")
                title = f"{meta['course_name']} {suffix}"
            elif payload.get("title"):
                title = payload.get("title")

    except Exception:
        # JSON 解析失败，视为纯文本
        content = ai_text

    if not content: content = ai_text  # 兜底
    if not title: title = generate_title_from_content(content, doc_type)

    return sanitize_filename(title), content
