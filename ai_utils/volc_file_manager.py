import os
import time
import mimetypes
from volcenginesdkarkruntime import Ark

# 支持的文件类型映射 (参考 ARK_doc.md)
SUPPORTED_MIME_TYPES = {
    # 图片
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp',
    # 视频
    '.mp4': 'video/mp4', '.avi': 'video/avi', '.mov': 'video/mov',
    # 文档
    '.pdf': 'application/pdf',
    # 文本类 (我们会将其内容读取出来作为 input_text 发送，不走 Files API，或者走纯文本逻辑)
    '.txt': 'text/plain', '.py': 'text/plain', '.java': 'text/plain', '.c': 'text/plain'
}


class VolcFileManager:
    def __init__(self, api_key, base_url):
        self.client = Ark(api_key=api_key, base_url=base_url)

    def upload_file(self, file_path):
        """上传文件并等待其变为 Active 状态"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_MIME_TYPES:
            return None  # 不支持的类型忽略

        mime_type = SUPPORTED_MIME_TYPES[ext]
        file_size = os.path.getsize(file_path)

        # 限制：单文件 512MB
        if file_size > 512 * 1024 * 1024:
            print(f"[VolcFile] 文件过大跳过: {file_path}")
            return None

        # 区分处理配置
        preprocess = None
        if mime_type.startswith('video'):
            # 视频抽帧配置，默认 0.5fps 节省 Token
            preprocess = {"video": {"fps": 0.5}}

        print(f"[VolcFile] Uploading {os.path.basename(file_path)}...")
        try:
            with open(file_path, "rb") as f:
                file_obj = self.client.files.create(
                    file=f,
                    purpose="user_data",
                    preprocess_configs=preprocess
                )

            # 轮询等待 Active
            file_id = file_obj.id
            max_retries = 30  # 约等待60秒
            for _ in range(max_retries):
                f_info = self.client.files.retrieve(file_id)
                if f_info.status == "active":
                    return file_id
                if f_info.status == "error":
                    print(f"[VolcFile] Upload failed: {f_info.status_details}")
                    return None
                time.sleep(2)

            return None  # 超时
        except Exception as e:
            print(f"[VolcFile] Exception: {e}")
            return None