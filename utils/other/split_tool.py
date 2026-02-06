import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import threading
import platform
import subprocess


class TextSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文档智能拆分工具")
        self.root.geometry("500x380")
        self.root.resizable(False, False)

        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 使用较为现代的主题

        # 变量
        self.file_path = tk.StringVar()
        self.chunk_size = tk.IntVar(value=2000)
        self.status_msg = tk.StringVar(value="请选择一个TXT文件开始")
        self.progress_var = tk.DoubleVar()

        self.create_widgets()

    def create_widgets(self):
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题区域
        title_label = ttk.Label(main_frame, text="TXT 文档智能拆分助手", font=("Microsoft YaHei", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="第一步：选择文件", padding="10")
        file_frame.pack(fill=tk.X, pady=5)

        entry_file = ttk.Entry(file_frame, textvariable=self.file_path, state='readonly')
        entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        btn_browse = ttk.Button(file_frame, text="浏览...", command=self.select_file)
        btn_browse.pack(side=tk.RIGHT)

        # 设置区域
        setting_frame = ttk.LabelFrame(main_frame, text="第二步：拆分设置", padding="10")
        setting_frame.pack(fill=tk.X, pady=10)

        lbl_size = ttk.Label(setting_frame, text="单文件目标字数：")
        lbl_size.pack(side=tk.LEFT)

        spin_size = ttk.Spinbox(setting_frame, from_=100, to=50000, increment=100, textvariable=self.chunk_size,
                                width=10)
        spin_size.pack(side=tk.LEFT, padx=5)

        lbl_hint = ttk.Label(setting_frame, text="(程序会尽量在标点处智能截断)", foreground="gray", font=("Arial", 9))
        lbl_hint.pack(side=tk.LEFT, padx=10)

        # 进度条
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=(10, 5))

        # 状态标签
        self.lbl_status = ttk.Label(main_frame, textvariable=self.status_msg, foreground="#555", font=("Arial", 9))
        self.lbl_status.pack(pady=(0, 10))

        # 执行按钮
        self.btn_run = ttk.Button(main_frame, text="开始拆分", command=self.start_processing_thread)
        self.btn_run.pack(fill=tk.X, ipady=5)

    def select_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filename:
            self.file_path.set(filename)
            self.status_msg.set("文件已就绪")

    def read_file_content(self, filepath):
        """尝试使用不同的编码读取文件"""
        encodings = ['utf-8', 'gbk', 'gb18030', 'utf-16']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise Exception("无法识别文件编码，请确保是标准的TXT文本文件。")

    def smart_split_text(self, text, limit):
        """
        智能拆分逻辑
        优先顺序：
        1. 寻找 limit 附近的段落结尾 (\n)
        2. 寻找 limit 附近的句子结尾 (。！？)
        3. 寻找 limit 附近的子句结尾 (，；)
        4. 强制截断
        """
        chunks = []
        start_idx = 0
        total_len = len(text)

        # 定义各类分隔符
        paragraph_delimiters = ['\n']
        sentence_delimiters = ['。', '！', '？', '!', '?', '”', '"']
        clause_delimiters = ['，', '；', ',', ';', '：', ':']

        while start_idx < total_len:
            end_idx = min(start_idx + limit, total_len)

            # 如果已经是最后一段，直接添加
            if end_idx == total_len:
                chunks.append(text[start_idx:end_idx])
                break

            # 截取一段缓冲区，我们在这个缓冲区里寻找最佳切割点
            # 这里的逻辑是：我们希望在 limit 附近切，但不要超过 limit 太多（或严格不超），
            # 这里的策略是：严格不超过 limit，向前回溯寻找最佳切割点

            current_slice = text[start_idx:end_idx]
            cut_offset = -1  # 默认在 end_idx 处切（相对偏移量）
            found_cut = False

            # 1. 尝试找换行符 (回溯查找)
            # 我们允许为了保持段落完整，牺牲大约 20% 的长度空间
            search_range_start = int(len(current_slice) * 0.8)

            # 反向搜索
            for i in range(len(current_slice) - 1, search_range_start, -1):
                char = current_slice[i]

                # 优先级1：段落
                if char in paragraph_delimiters:
                    cut_offset = i + 1  # 保留换行符
                    found_cut = True
                    break

            # 优先级2：句子结束 (如果没有找到段落)
            if not found_cut:
                for i in range(len(current_slice) - 1, search_range_start, -1):
                    if current_slice[i] in sentence_delimiters:
                        cut_offset = i + 1
                        found_cut = True
                        break

            # 优先级3：逗号等 (如果没找到句子结束)
            if not found_cut:
                for i in range(len(current_slice) - 1, search_range_start, -1):
                    if current_slice[i] in clause_delimiters:
                        cut_offset = i + 1
                        found_cut = True
                        break

            # 如果以上都没找到（比如是一大段无标点文字），或者找到了但位置太远
            # 这时 found_cut 为 False，cut_offset 保持为 -1 (即 length)
            # 或者我们在这里使用 current_slice 的长度

            real_cut_pos = start_idx + (cut_offset if found_cut else len(current_slice))

            # 确保不会死循环（如果切分位置等于开始位置，强制+1）
            if real_cut_pos <= start_idx:
                real_cut_pos = start_idx + limit

            chunks.append(text[start_idx:real_cut_pos])
            start_idx = real_cut_pos

            # 更新进度回调 (仅作为估算)
            progress = (start_idx / total_len) * 50  # 读取占50，写入占50? 不，这里只算处理
            # 实际进度在主循环更新更平滑

        return chunks

    def start_processing_thread(self):
        if not self.file_path.get():
            messagebox.showwarning("提示", "请先选择一个文件！")
            return

        # 禁用按钮防止重复点击
        self.btn_run.config(state=tk.DISABLED)
        self.status_msg.set("正在读取并分析文件...")

        # 开启新线程运行任务
        threading.Thread(target=self.process_file, daemon=True).start()

    def process_file(self):
        try:
            source_path = self.file_path.get()
            limit = self.chunk_size.get()

            # 1. 读取文件
            content = self.read_file_content(source_path)
            self.root.after(0, lambda: self.progress_var.set(20))
            self.root.after(0, lambda: self.status_msg.set(f"读取成功，共 {len(content)} 字，正在计算拆分点..."))

            # 2. 智能拆分
            chunks = self.smart_split_text(content, limit)
            self.root.after(0, lambda: self.progress_var.set(60))

            # 3. 创建输出目录
            dir_name = os.path.dirname(source_path)
            base_name = os.path.basename(source_path).rsplit('.', 1)[0]
            output_dir = os.path.join(dir_name, f"{base_name}_拆分结果")

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 4. 写入文件
            total_chunks = len(chunks)
            digits = len(str(total_chunks))  # 用于文件名补零对齐

            for i, chunk in enumerate(chunks):
                chunk_id = self.make_chunk_id(i, digits)
                file_name = f"{base_name}_{chunk_id}.txt"
                file_path = os.path.join(output_dir, file_name)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"[chunk_id: {chunk_id}]" + "\n\n" + chunk)

                # 更新进度
                current_percent = 60 + ((i + 1) / total_chunks * 40)
                self.root.after(0, lambda p=current_percent: self.progress_var.set(p))
                self.root.after(0, lambda i=i: self.status_msg.set(f"正在写入第 {i + 1}/{total_chunks} 个文件..."))

            # 5. 完成
            self.root.after(0, lambda: self.finish_process(output_dir, total_chunks))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
            self.root.after(0, lambda: self.reset_ui())

    def make_chunk_id(self, index, digits):
        """
        形如： S0001, S0002, ... 这里的 S 可以代表 Sentence，也可以理解为 Split，后面是补零的数字
        """
        return f"S{str(index + 1).zfill(digits+1)}"

    def finish_process(self, output_dir, count):
        self.progress_var.set(100)
        self.status_msg.set("拆分完成！")
        self.btn_run.config(state=tk.NORMAL)

        result = messagebox.askyesno("完成", f"成功拆分为 {count} 个文件！\n是否打开输出文件夹？")
        if result:
            self.open_folder(output_dir)

    def reset_ui(self):
        self.btn_run.config(state=tk.NORMAL)
        self.status_msg.set("就绪")
        self.progress_var.set(0)

    def open_folder(self, path):
        """跨平台打开文件夹"""
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])


if __name__ == "__main__":
    root = tk.Tk()
    app = TextSplitterApp(root)
    root.mainloop()
