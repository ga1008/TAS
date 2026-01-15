# services/file_service.py
import os
import re

import PyPDF2
from docx import Document

from config import Config
from extensions import db
from utils.common import calculate_file_hash, is_content_garbage


class FileService:
    @staticmethod
    def get_real_workspace_path(class_id):
        """获取班级工作区绝对路径"""
        ws_path = os.path.join(Config.WORKSPACE_FOLDER, str(class_id))
        if not os.path.exists(ws_path):
            os.makedirs(ws_path)
        return ws_path

    @staticmethod
    def extract_text_from_file(file_path):
        """从文件提取文本 (合并了原 app.py 中的逻辑)"""
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
        try:
            if ext == '.pdf':
                reader = PyPDF2.PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted: text += extracted + "\n"
            elif ext == '.docx':
                doc = Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            elif ext == '.doc':
                # 尝试纯文本读取兜底 HTML/XML 伪装的 doc
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if '<html' in content.lower() or '<?xml' in content.lower():
                        text = re.sub(r'<[^>]+>', '\n', content)
                    else:
                        text = content
            else:
                # 文本文件处理
                encodings = ['utf-8', 'gb18030', 'gbk', 'big5', 'latin1']
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            text = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                if not text:  # 兜底
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
        except Exception as e:
            return False, f"解析异常: {str(e)}"

        if is_content_garbage(text):
            return False, "文件似乎是二进制格式或已损坏（出现乱码）。"

        if text: text = text.replace('\x00', '')
        if not text.strip(): return False, "解析结果为空"

        return True, text

    @staticmethod
    def handle_file_upload_or_reuse(file_obj, existing_file_id, user_id):
        """处理文件上传或复用逻辑"""
        if existing_file_id:
            record = db.get_file_by_id(existing_file_id)
            if record: return record['physical_path'], record['original_name']
            raise Exception("选中的文件记录不存在")

        if file_obj and file_obj.filename:
            f_hash = calculate_file_hash(file_obj)
            existing_record = db.get_file_by_hash(f_hash)

            # 即使数据库有记录，如果物理文件不存在，也需要重新保存
            if existing_record and os.path.exists(existing_record['physical_path']):
                return existing_record['physical_path'], file_obj.filename

            ext = os.path.splitext(file_obj.filename)[1]
            physical_path = os.path.normpath(os.path.join(Config.FILE_REPO_FOLDER, f"{f_hash}{ext}"))
            file_obj.save(physical_path)

            db.save_file_asset(f_hash, file_obj.filename, os.path.getsize(physical_path), physical_path, user_id)
            return physical_path, file_obj.filename

        return None, None
