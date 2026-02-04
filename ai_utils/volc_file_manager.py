import os
import time
import mimetypes
from volcenginesdkarkruntime import Ark

# 参考 ARC_doc.md 完善 MIME 类型映射
SUPPORTED_MIME_TYPES = {
    # 图片 (Files API 支持图片上传，建议大图走 Files API)
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp',
    '.tiff': 'image/tiff', '.heic': 'image/heic', '.heif': 'image/heif',
    # 视频
    '.mp4': 'video/mp4', '.avi': 'video/avi', '.mov': 'video/mov',
    # 文档
    '.pdf': 'application/pdf',
    # 文本类通常直接读取内容作为 Prompt，不走 Files API，除非作为知识库文件
    # 这里保留是为了兼容性，但 Grader 核心逻辑中应读取文本内容
}


class VolcFileManager:
    def __init__(self, api_key, base_url):
        self.client = Ark(api_key=api_key, base_url=base_url)

    def upload_file(self, file_path):
        """上传文件并等待其变为 Active 状态"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_MIME_TYPES:
            print(f"[VolcFile] 不支持的文件类型: {ext}")
            return None

        mime_type = SUPPORTED_MIME_TYPES[ext]

        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            return None

        # 限制：单文件 512MB (官方限制)
        if file_size > 512 * 1024 * 1024:
            print(f"[VolcFile] 文件过大跳过: {file_path}")
            return None

        # 预处理配置
        preprocess = None
        if mime_type.startswith('video'):
            # 视频抽帧配置，0.5fps 兼顾细节与 Token 消耗
            preprocess = {"video": {"fps": 0.5}}

        # 图片/PDF 不需要额外的 preprocess_configs，SDK 会自动处理

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
            # 视频可能处理较慢，PDF/图片通常很快，设置动态超时
            max_retries = 60 if mime_type.startswith('video') else 20

            for _ in range(max_retries):
                f_info = self.client.files.retrieve(file_id)
                if f_info.status == "active":
                    print(f"[VolcFile] File Active: {file_id}")
                    return file_id
                if f_info.status == "error":
                    print(f"[VolcFile] Upload failed: {f_info.status_details}")
                    return None
                time.sleep(2)  # 间隔2秒轮询

            print(f"[VolcFile] Wait processing timeout: {file_id}")
            return None  # 超时
        except Exception as e:
            print(f"[VolcFile] Exception: {e}")
            return None
