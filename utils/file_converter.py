import sys
import subprocess
import os
import platform


def convert_to_pdf(input_path, output_dir=None):
    """
    将 Word 文档 (.docx, .doc) 转换为 PDF。
    依赖:
    1. Linux: 需要安装 LibreOffice (apt-get install libreoffice)
    2. Windows: 需要安装 Microsoft Word，并 pip install docx2pdf pywin32
    """
    if not output_dir:
        output_dir = os.path.dirname(input_path)

    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)

    # 目标 PDF 路径
    target_pdf_path = os.path.join(output_dir, f"{name}.pdf")

    # 如果已经是 PDF，直接返回
    if ext.lower() == '.pdf':
        return input_path

    try:
        # === Windows 环境使用 docx2pdf (依赖 MS Word) ===
        if platform.system() == "Windows":
            # [关键修复] 引入 pythoncom 处理多线程 COM 调用
            import pythoncom

            # 在当前线程初始化 COM 库
            pythoncom.CoInitialize()

            try:
                from docx2pdf import convert
                print(f"[Converter] Converting {filename} to PDF using docx2pdf...")

                # docx2pdf 可能会因为 Word 弹窗或卡死而报错，加一层保护
                convert(input_path, target_pdf_path)
                return target_pdf_path
            except Exception as e:
                print(f"[Converter] Windows Conversion Error: {e}")
                return None
            finally:
                # 释放 COM 资源，防止内存泄漏
                pythoncom.CoUninitialize()

        # === Linux 环境使用 LibreOffice (Headless) ===
        else:
            # 检查 libreoffice 是否存在
            # 常用命令: libreoffice, libreoffice7.x, soffice
            cmd = "libreoffice"
            # 简单的检查逻辑，实际生产环境建议在 Dockerfile 中保证环境

            print(f"[Converter] Converting {filename} to PDF using LibreOffice...")
            # --outdir 指定输出目录
            result = subprocess.run(
                [cmd, '--headless', '--convert-to', 'pdf', '--outdir', output_dir, input_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode != 0:
                print(f"[Converter] LibreOffice conversion failed: {result.stderr.decode()}")
                return None

            return target_pdf_path

    except Exception as e:
        print(f"[Converter] Conversion Exception: {e}")
        return None