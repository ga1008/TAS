import os
import random
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd


def select_excel_file():
    """弹出文件选择对话框，让用户选择Excel文件"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    file_path = filedialog.askopenfilename(
        title="选择名单Excel文件",
        filetypes=[("Excel files", "*.xls *.xlsx")]
    )
    return file_path


def select_folder():
    """弹出文件夹选择对话框，让用户选择父文件夹"""
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="选择包含待修改文件夹的父文件夹")
    return folder_path


def read_excel_names(file_path):
    """
    读取Excel文件，提取学号和姓名列，返回学号-姓名列表
    如果缺少必要列，返回None并弹出错误
    """
    try:
        df = pd.read_excel(file_path, dtype=str)  # 以字符串类型读取，避免学号前导0丢失
    except Exception as e:
        messagebox.showerror("错误", f"读取Excel文件失败：{e}")
        return None

    # 检查列是否存在（忽略大小写和空格）
    required_cols = {'学号', '姓名'}
    df_cols = {col.strip() for col in df.columns}
    if not required_cols.issubset(df_cols):
        missing = required_cols - df_cols
        messagebox.showerror("错误", f"Excel文件中缺少列：{', '.join(missing)}")
        return None

    # 提取数据并去除可能的空行
    df = df[['学号', '姓名']].dropna()
    if df.empty:
        messagebox.showerror("错误", "Excel文件中没有有效数据")
        return None

    # 组合成“学号-姓名”列表
    names = [f"{row['学号'].strip()}-{row['姓名'].strip()}" for _, row in df.iterrows()]
    return names


def get_subfolders(parent_folder):
    """获取父文件夹下的所有直接子文件夹（排除文件）"""
    if not os.path.isdir(parent_folder):
        return []
    all_items = os.listdir(parent_folder)
    folders = []
    for item in all_items:
        full_path = os.path.join(parent_folder, item)
        if os.path.isdir(full_path):
            folders.append(item)
    return folders


def delete_extra_folders(parent_folder, folders_to_delete):
    """删除指定的文件夹列表"""
    for folder_name in folders_to_delete:
        folder_path = os.path.join(parent_folder, folder_name)
        try:
            shutil.rmtree(folder_path)
            print(f"已删除多余文件夹：{folder_name}")
        except Exception as e:
            print(f"删除文件夹 {folder_name} 失败：{e}")


def rename_folders(parent_folder, folders, new_names, progress_callback=None):
    """
    按顺序重命名文件夹
    :param parent_folder: 父文件夹路径
    :param folders: 当前文件夹名称列表（已排序）
    :param new_names: 新名称列表（按Excel顺序）
    :param progress_callback: 进度回调函数，接收当前进度和总数
    :return: (成功数, 失败列表)
    """
    success = 0
    failures = []
    total = len(folders)
    for i, (old_name, new_name) in enumerate(zip(folders, new_names)):
        old_path = os.path.join(parent_folder, old_name)
        new_path = os.path.join(parent_folder, new_name)
        try:
            # 如果目标文件夹已存在，则添加后缀以避免覆盖（这里简单跳过，可根据需求修改）
            if os.path.exists(new_path):
                raise Exception(f"目标文件夹 {new_name} 已存在")
            os.rename(old_path, new_path)
            success += 1
        except Exception as e:
            failures.append((old_name, new_name, str(e)))
        if progress_callback:
            progress_callback(i + 1, total)
    return success, failures


def show_progress_window(total):
    """创建一个进度窗口，返回进度条和标签对象"""
    progress_win = tk.Toplevel()
    progress_win.title("正在重命名")
    progress_win.geometry("400x150")
    progress_win.resizable(False, False)

    label = ttk.Label(progress_win, text="准备开始...")
    label.pack(pady=10)

    progress_bar = ttk.Progressbar(progress_win, length=300, mode='determinate', maximum=total)
    progress_bar.pack(pady=10)

    return progress_win, progress_bar, label


def update_progress(progress_win, progress_bar, label, current, total):
    """更新进度显示"""
    progress_bar['value'] = current
    label.config(text=f"正在处理 {current}/{total}")
    progress_win.update()


def main():
    # 1. 选择Excel文件
    excel_path = select_excel_file()
    if not excel_path:
        messagebox.showinfo("提示", "未选择Excel文件，程序退出")
        return

    # 2. 读取Excel，获取新名称列表
    new_names = read_excel_names(excel_path)
    if new_names is None:
        return
    total_names = len(new_names)

    # 3. 选择父文件夹
    parent_folder = select_folder()
    if not parent_folder:
        messagebox.showinfo("提示", "未选择父文件夹，程序退出")
        return

    # 4. 获取当前子文件夹
    current_folders = get_subfolders(parent_folder)
    current_count = len(current_folders)

    # 5. 数量检查
    if current_count < total_names:
        messagebox.showerror("错误",
                             f"文件夹数量不足：当前有 {current_count} 个文件夹，名单需要 {total_names} 个。\n请添加文件夹后重试。")
        return
    elif current_count > total_names:
        # 随机删除多余的文件夹
        extra_count = current_count - total_names
        # 随机选择要删除的文件夹
        folders_to_delete = random.sample(current_folders, extra_count)
        # 确认删除
        confirm = messagebox.askyesno("确认删除",
                                      f"当前有 {current_count} 个文件夹，名单需要 {total_names} 个。\n"
                                      f"将随机删除 {extra_count} 个文件夹：\n{', '.join(folders_to_delete)}\n"
                                      f"是否继续？")
        if not confirm:
            messagebox.showinfo("提示", "用户取消操作")
            return
        delete_extra_folders(parent_folder, folders_to_delete)
        # 重新获取剩余文件夹列表
        current_folders = get_subfolders(parent_folder)
        # 再次检查数量（防止删除失败）
        if len(current_folders) != total_names:
            messagebox.showerror("错误", "删除后文件夹数量仍不匹配，请手动检查")
            return
        messagebox.showinfo("提示", f"已删除 {extra_count} 个多余文件夹")

    # 6. 对文件夹列表排序（按名称），以便与Excel顺序对应
    current_folders.sort()
    # 如果希望用户自定义顺序，可以在此处添加逻辑，但按需求简化处理

    # 7. 创建进度窗口
    progress_win, progress_bar, label = show_progress_window(total_names)

    # 8. 定义进度回调
    def progress_callback(current, total):
        update_progress(progress_win, progress_bar, label, current, total)

    # 9. 执行重命名
    success, failures = rename_folders(parent_folder, current_folders, new_names, progress_callback)

    # 10. 关闭进度窗口
    progress_win.destroy()

    # 11. 显示结果
    result_msg = f"重命名完成！成功：{success}，失败：{len(failures)}"
    if failures:
        fail_detail = "\n".join([f"{old} -> {new}: {err}" for old, new, err in failures])
        result_msg += f"\n失败详情：\n{fail_detail}"
    messagebox.showinfo("完成", result_msg)


if __name__ == "__main__":
    main()
