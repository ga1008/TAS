import os
import sys
import shutil
import time
import tempfile
import zipfile
import patoolib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from collections import Counter


# ===========================
# 核心处理逻辑 (独立函数以支持多进程)
# ===========================

def extract_archive(args):
    """
    解压单个文件的任务函数
    """
    file_path, extract_root = args
    filename = os.path.basename(file_path)
    # 创建以文件名命名的解压目录（去除后缀）
    folder_name = os.path.splitext(filename)[0]
    target_dir = os.path.join(extract_root, folder_name)

    os.makedirs(target_dir, exist_ok=True)

    try:
        # 使用 patoolib 进行解压，它会自动寻找系统的 winrar/7zip
        # 屏蔽输出以防控制台乱码
        patoolib.extract_archive(file_path, outdir=target_dir, verbosity=-1)
        return (True, f"成功解压: {filename}", target_dir, folder_name)
    except Exception as e:
        return (False, f"解压失败 {filename}: {str(e)}", None, None)


def process_student_files(args):
    """
    重新打包单个学生的文件的任务函数
    """
    source_dir, original_name, output_dir, allowed_extensions = args

    new_zip_name = f"{original_name}.zip"
    new_zip_path = os.path.join(output_dir, new_zip_name)

    files_to_pack = []

    # 1. 扫描符合条件的文件
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            # 获取后缀，处理无后缀文件
            _, ext = os.path.splitext(file)
            if ext == '':
                ext = '无后缀'
            else:
                ext = ext.lower()

            if ext in allowed_extensions:
                full_path = os.path.join(root, file)
                files_to_pack.append(full_path)

    if not files_to_pack:
        return (False, f"跳过 {original_name}: 未找到指定类型的文件")

    try:
        # 2. 压缩逻辑 (扁平化)
        with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            added_filenames = set()

            for file_path in files_to_pack:
                # 获取原始文件名
                base_name = os.path.basename(file_path)
                final_name = base_name

                # 处理重名文件 (例如 src/A.java 和 bin/A.java)
                # 如果扁平化后名字冲突，添加 _1, _2 后缀
                counter = 1
                name_part, ext_part = os.path.splitext(base_name)
                while final_name in added_filenames:
                    final_name = f"{name_part}_{counter}{ext_part}"
                    counter += 1

                added_filenames.add(final_name)
                # 写入压缩包，arcname 参数决定了在压缩包内的路径(这里只给文件名，实现扁平化)
                zf.write(file_path, arcname=final_name)

        return (True, f"已处理并重打包: {new_zip_name}")
    except Exception as e:
        return (False, f"打包失败 {original_name}: {str(e)}")


# ===========================
# GUI 界面类
# ===========================

class HomeworkProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学生作业批量预处理工具 (Win版)")
        self.root.geometry("700x550")

        # 状态变量
        self.work_dir = tk.StringVar()
        self.temp_dir = None
        self.extracted_info = []  # 存储 (temp_path, original_name)

        self.setup_ui()

    def setup_ui(self):
        # 1. 顶部选择区域
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill=tk.X, padx=10)

        tk.Label(top_frame, text="作业所在文件夹:").pack(side=tk.LEFT)
        tk.Entry(top_frame, textvariable=self.work_dir, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="浏览...", command=self.select_folder).pack(side=tk.LEFT)

        # 2. 操作按钮区域
        btn_frame = tk.Frame(self.root, pady=5)
        btn_frame.pack(fill=tk.X, padx=10)

        self.btn_start = tk.Button(btn_frame, text="开始处理", command=self.start_processing, bg="#dddddd",
                                   state=tk.DISABLED)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        tk.Label(btn_frame, text="注意：处理将覆盖或新建zip文件，请做好备份", fg="red").pack(side=tk.LEFT, padx=10)

        # 3. 日志区域
        log_frame = tk.LabelFrame(self.root, text="处理日志", padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 4. 进度条
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=10)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.work_dir.set(folder)
            self.btn_start.config(state=tk.NORMAL)
            self.log(f"已选择目录: {folder}")
            self.log("提示: 请确保电脑已安装 WinRAR 或 7-Zip，否则无法处理 .rar 文件。")

    def start_processing(self):
        folder = self.work_dir.get()
        if not os.path.exists(folder):
            messagebox.showerror("错误", "文件夹不存在")
            return

        # 禁用按钮防止重复点击
        self.btn_start.config(state=tk.DISABLED)
        self.log("--- 开始扫描并解压文件 ---")

        # 异步执行，防止界面卡死
        self.root.after(100, self.step_1_extract)

    def step_1_extract(self):
        folder = self.work_dir.get()

        # 1. 扫描文件
        archives = []
        for f in os.listdir(folder):
            if f.lower().endswith(('.zip', '.rar')):
                archives.append(os.path.join(folder, f))

        if not archives:
            self.log("未找到压缩包(.zip/.rar)")
            self.btn_start.config(state=tk.NORMAL)
            return

        self.log(f"找到 {len(archives)} 个压缩包，正在解压...")

        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="homework_proc_")

        # 准备任务
        tasks = [(f, self.temp_dir) for f in archives]

        # 多进程解压
        self.extracted_info = []  # 重置
        cpu_count = min(multiprocessing.cpu_count(), len(tasks))

        self.progress['maximum'] = len(tasks)
        self.progress['value'] = 0

        success_count = 0

        with ProcessPoolExecutor(max_workers=cpu_count) as executor:
            for result in executor.map(extract_archive, tasks):
                success, msg, target_dir, folder_name = result
                self.log(msg)
                self.progress['value'] += 1
                self.root.update()

                if success:
                    success_count += 1
                    self.extracted_info.append((target_dir, folder_name))

        self.log(f"--- 解压完成，成功: {success_count}/{len(tasks)} ---")

        if success_count > 0:
            # 进入下一步：统计文件类型
            self.step_2_analyze_types()
        else:
            messagebox.showerror("错误", "没有文件被成功解压，请检查压缩包格式或WinRAR/7z是否安装。")
            self.cleanup()

    def step_2_analyze_types(self):
        self.log("正在分析文件类型...")
        all_extensions = Counter()

        for extract_path, _ in self.extracted_info:
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext == '':
                        ext = '无后缀'
                    else:
                        ext = ext.lower()
                    all_extensions[ext] += 1

        # 弹出窗口让用户选择
        self.show_extension_selector(all_extensions)

    def show_extension_selector(self, counter):
        top = tk.Toplevel(self.root)
        top.title("选择要保留的文件类型")
        top.geometry("400x500")
        top.transient(self.root)
        top.grab_set()  # 模态窗口

        tk.Label(top, text="请勾选需要保留的文件类型：", font=("Arial", 10, "bold")).pack(pady=10)

        # 滚动区域
        canvas = tk.Canvas(top)
        scrollbar = tk.Scrollbar(top, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 生成复选框
        check_vars = {}

        # 默认推荐保留的 Eclipse web 项目常见类型
        recommended = {'.java', '.jsp', '.html', '.css', '.js', '.xml', '.sql', '.txt', '.properties'}

        # 按数量排序显示
        for ext, count in counter.most_common():
            var = tk.BooleanVar()
            # 如果是推荐类型，默认勾选
            if ext in recommended:
                var.set(True)
            check_vars[ext] = var

            chk = tk.Checkbutton(scroll_frame, text=f"{ext} (共 {count} 个文件)", variable=var, anchor='w')
            chk.pack(fill='x', padx=20)

        def on_confirm():
            selected = [ext for ext, var in check_vars.items() if var.get()]
            if not selected:
                messagebox.showwarning("提示", "请至少选择一种文件类型")
                return
            top.destroy()
            self.step_3_repack(selected)

        tk.Button(top, text="确认并开始处理", command=on_confirm, bg="#4CAF50", fg="white", height=2).pack(fill='x',
                                                                                                           side='bottom')

    def step_3_repack(self, allowed_extensions):
        self.log(f"--- 开始重组打包，保留类型: {allowed_extensions} ---")
        self.log("正在执行：过滤文件 -> 扁平化目录 -> 压缩 -> 重命名...")

        output_dir = os.path.join(self.work_dir.get(), "已处理作业")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        tasks = []
        for extract_path, original_name in self.extracted_info:
            tasks.append((extract_path, original_name, output_dir, allowed_extensions))

        self.progress['maximum'] = len(tasks)
        self.progress['value'] = 0

        # 多进程处理打包
        cpu_count = min(multiprocessing.cpu_count(), len(tasks))
        with ProcessPoolExecutor(max_workers=cpu_count) as executor:
            for result in executor.map(process_student_files, tasks):
                success, msg = result
                self.log(msg)
                self.progress['value'] += 1
                self.root.update()

        self.log("--- 所有处理结束 ---")
        self.log(f"处理后的文件保存在: {output_dir}")
        messagebox.showinfo("完成", f"处理完成！\n文件已保存至：\n{output_dir}")

        self.cleanup()
        self.btn_start.config(state=tk.NORMAL)

    def cleanup(self):
        # 清理临时文件夹
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.log("临时文件已清理。")
            except Exception as e:
                self.log(f"警告: 临时文件清理失败: {e}")


if __name__ == "__main__":
    # 必须在主模块检查 patool 是否可用（或提示用户）
    # 支持 Windows 的多进程调用保护
    multiprocessing.freeze_support()

    root = tk.Tk()
    app = HomeworkProcessorApp(root)
    root.mainloop()
