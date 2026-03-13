import json
import os
import re
import shutil
import stat
import subprocess
import time
import tkinter as tk
from tkinter import filedialog

import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.theme import Theme

# 自定义终端输出主题
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green"
})
console = Console(theme=custom_theme)


def check_git_installed():
    """检查系统是否安装了 Git"""
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def select_paths():
    """弹窗选择 Excel 文件和目标文件夹"""
    root = tk.Tk()
    root.withdraw()

    console.print("[info]请在弹出的窗口中选择包含学生仓库链接的 Excel 文件...[/info]")
    excel_path = filedialog.askopenfilename(
        title="选择学生作业 Excel 文件",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )

    if not excel_path:
        console.print("[error]未选择 Excel 文件，程序退出。[/error]")
        return None, None

    console.print("[info]请选择存放学生仓库的本地文件夹（取消则默认在 Excel 同级目录下新建文件夹）...[/info]")
    target_dir = filedialog.askdirectory(title="选择存放仓库的文件夹")

    if not target_dir:
        base_name = os.path.splitext(os.path.basename(excel_path))[0]
        target_dir = os.path.join(os.path.dirname(excel_path), f"{base_name}_作业收集")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

    return excel_path, target_dir


def clean_gitee_url(raw_url):
    """清洗学生提交的混乱 URL"""
    raw_url = str(raw_url).strip()
    if pd.isna(raw_url) or not raw_url.startswith("http"):
        return None, None

    match = re.search(r'(https?://gitee\.com/[^/]+/[^/?#\.]+)', raw_url)
    if match:
        base_url = match.group(1)
        clean_url = f"{base_url}.git"
        repo_name = base_url.split("/")[-1]
        return clean_url, repo_name
    return raw_url, "unknown_repo"


def load_student_data(excel_path):
    """【全新优化】智能嗅探并读取多种 Excel 数据格式"""
    try:
        # 不指定表头读取全表
        df = pd.read_excel(excel_path, header=None)
        students = []

        url_col_idx = -1
        start_row = 0

        # 1. 寻找包含 "http" 的单元格，确定链接所在的列和数据起始行
        for col in df.columns:
            http_mask = df[col].astype(str).str.contains('http', case=False, na=False)
            if http_mask.any():
                url_col_idx = col
                start_row = http_mask.idxmax()  # 找到第一个包含 http 的行索引
                break

        if url_col_idx == -1:
            console.print("[error]无法在表格中识别出包含 'http' 的仓库链接列。[/error]")
            return None

        id_col_idx = -1
        name_col_idx = -1

        # 2. 向上嗅探（最多往上找两行），看看有没有“学号”和“姓名”的表头
        header_search_start = max(0, start_row - 2)
        for r in range(header_search_start, start_row):
            for c in df.columns:
                cell_val = str(df.iloc[r, c]).strip()
                if '学号' in cell_val:
                    id_col_idx = c
                elif '姓名' in cell_val:
                    name_col_idx = c

        # 3. 开始提取数据
        for idx in range(start_row, len(df)):
            raw_url = str(df.iloc[idx, url_col_idx]).strip()
            if not raw_url.startswith("http"):
                continue  # 过滤掉可能穿插的空行或备注

            stu_id = ""
            if id_col_idx != -1 and pd.notna(df.iloc[idx, id_col_idx]):
                stu_id = str(df.iloc[idx, id_col_idx]).strip()
                if stu_id.endswith(".0"): stu_id = stu_id[:-2]

            name = ""
            if name_col_idx != -1 and pd.notna(df.iloc[idx, name_col_idx]):
                name = str(df.iloc[idx, name_col_idx]).strip()

            students.append({
                '学号': stu_id,
                '姓名': name,
                '仓库链接': raw_url
            })

        return students
    except Exception as e:
        console.print(f"[error]读取 Excel 文件失败: {e}[/error]")
        return None


def get_status_file_path(target_dir):
    return os.path.join(target_dir, ".clone_status.json")


def load_status(target_dir):
    status_file = get_status_file_path(target_dir)
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_status(target_dir, status_dict):
    status_file = get_status_file_path(target_dir)
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status_dict, f, ensure_ascii=False, indent=4)


def clone_repository(url, target_path, max_retries=3):
    """执行 Git Clone 并带有重试机制（已修复 Windows GBK 解码报错）"""
    if os.path.exists(target_path) and os.listdir(target_path):
        return True, "文件夹已存在且不为空"

    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(
                ["git", "clone", url, target_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',  # 强制使用 UTF-8
                errors='ignore',  # 忽略非法字符
                timeout=60
            )

            if result.returncode == 0:
                return True, "成功"
            else:
                error_msg = result.stderr.strip()
                if "not found" in error_msg.lower() or "fatal: repository" in error_msg.lower():
                    return False, f"仓库不存在或无权限访问"

                if attempt < max_retries:
                    time.sleep(2)
                else:
                    return False, f"重试{max_retries}次后失败: {error_msg[:50]}..."

        except subprocess.TimeoutExpired:
            if attempt < max_retries:
                time.sleep(2)
            else:
                return False, "下载超时"
        except Exception as e:
            return False, str(e)


def remove_readonly(func, path, excinfo):
    """强制解除只读文件的权限并重试删除"""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def cleanup_git_folders(target_dir):
    """遍历下载目录，统一清理所有的 .git 隐藏文件夹"""
    console.print("\n[info]开始执行收尾工作：清理 .git 等版本控制目录...[/info]")
    cleaned_count = 0
    rm_dirs = ['.git', '.idea', '__pycache__', '.vscode', '.settings', '.DS_Store', 'build', 'dist', 'node_modules', 'venv', 'env', '.metadata']
    for root, dirs, files in os.walk(target_dir):
        for rm_dir in rm_dirs:
            if rm_dir in dirs:
                rm_path = os.path.join(root, rm_dir)
                try:
                    shutil.rmtree(rm_path, onerror=remove_readonly)
                    cleaned_count += 1
                except Exception as e:
                    console.print(f"[warning]清理 {rm_path} 失败: {e}[/warning]")

    if cleaned_count > 0:
        console.print(f"[success]已成功为您清理 {cleaned_count} 个无用的目录，释放了存储空间！[/success]")


def main():
    console.rule("[bold cyan]软工作业 Gitee 仓库自动收集工具 (智能多格式版)[/bold cyan]")

    if not check_git_installed():
        console.print("[error]未检测到 Git，请先安装 Git 并配置环境变量！[/error]")
        return

    excel_path, target_dir = select_paths()
    if not excel_path:
        return

    console.print(f"[info]读取数据文件:[/info] {excel_path}")
    console.print(f"[info]目标存储目录:[/info] {target_dir}")

    students = load_student_data(excel_path)
    if not students:
        return

    total_students = len(students)
    console.print(f"[success]成功识别 {total_students} 条仓库记录！[/success]\n")

    status_dict = load_status(target_dir)

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console
    ) as progress:

        clone_task = progress.add_task("[cyan]正在克隆仓库...", total=total_students)

        success_count = 0
        failed_list = []

        for student in students:
            stu_id = student['学号']
            name = student['姓名']
            raw_url = student['仓库链接']

            clean_url, repo_name = clean_gitee_url(raw_url)

            # 使用清洗后的 URL 作为断点续传的唯一主键（适应没有学号的情况）
            status_key = clean_url if clean_url else raw_url

            if status_key in status_dict and status_dict[status_key]['status'] == 'success':
                success_count += 1
                progress.advance(clone_task)
                continue

            if not clean_url:
                display_name = name if name else raw_url
                failed_list.append((display_name, "无效的 URL"))
                status_dict[status_key] = {'name': display_name, 'url': raw_url, 'status': 'failed',
                                           'reason': '无效的 URL'}
                progress.advance(clone_task)
                continue

            # 动态拼接文件夹名称
            folder_parts = []
            if stu_id: folder_parts.append(stu_id)
            if name: folder_parts.append(name)
            folder_parts.append(repo_name)

            folder_name = "-".join(folder_parts)
            folder_name = re.sub(r'[\\/*?:"<>|]', "", folder_name)
            target_path = os.path.join(target_dir, folder_name)

            display_task_name = name if name else repo_name
            progress.update(clone_task, description=f"[cyan]正在下载: {display_task_name} ...")

            is_success, msg = clone_repository(clean_url, target_path)

            if is_success:
                status_dict[status_key] = {'name': display_task_name, 'url': clean_url, 'status': 'success',
                                           'path': folder_name}
                success_count += 1
            else:
                status_dict[status_key] = {'name': display_task_name, 'url': clean_url, 'status': 'failed',
                                           'reason': msg}
                failed_list.append((display_task_name, msg))

            save_status(target_dir, status_dict)
            progress.advance(clone_task)
            time.sleep(0.5)

    console.rule("[bold cyan]任务完成报告[/bold cyan]")
    console.print(
        f"总计: {total_students} | [success]成功: {success_count}[/success] | [error]失败: {len(failed_list)}[/error]")

    if failed_list:
        console.print("\n[warning]以下仓库下载失败，请手动核对：[/warning]")
        for display_name, reason in failed_list:
            console.print(f"- {display_name}: {reason}")
    else:
        console.print("\n[success]🎉 太棒了！所有仓库均已成功下载！[/success]")

    # 执行清理工作
    cleanup_git_folders(target_dir)


if __name__ == "__main__":
    main()
