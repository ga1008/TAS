"""
导出文件名生成工具

支持两种模式：
1. 模板模式：根据预定义模板生成文件名
2. AI 模式：调用 AI 助手生成更智能的文件名
"""

import os
import re
from typing import Dict, Optional, Tuple
from urllib.parse import quote


class FilenameGenerator:
    """智能文件名生成器"""

    # 预定义的文件名模板
    TEMPLATES = {
        # Word 文档模板
        'word': "{course_name}_{class_name}_成绩单.docx",
        'word_with_semester': "{semester}_{course_name}_{class_name}_成绩单.docx",

        # Excel 登分表模板
        'excel_score_sheet': "{course_name}_{class_name}_考核登分表.xlsx",
        'excel_score_sheet_with_semester': "{semester}《{course_name}》考核登分表-{class_name}.xlsx",
        'excel_simple': "{class_name}_{course_name}_成绩表.xlsx",
        'excel_with_semester': "{semester}-{class_name}-{course_name}-成绩表.xlsx",
    }

    @staticmethod
    def clean_filename(name: str) -> str:
        """
        清理文件名中的非法字符

        Args:
            name: 原始文件名

        Returns:
            清理后的安全文件名
        """
        # 移除或替换 Windows 文件系统不允许的字符
        # 不允许的字符: < > : " / \ | ? *
        # 替换为下划线或删除
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # 移除多余的空格和点
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'\.+', '.', name)
        # 去除首尾的点和空格
        name = name.strip('. ')
        # 如果为空，返回默认名称
        return name if name else "未命名"

    @staticmethod
    def extract_metadata(file_record: Dict, form_data: Dict = None) -> Dict[str, str]:
        """
        从文件记录和表单数据中提取元数据

        Args:
            file_record: 数据库文件记录
            form_data: 用户填写的表单数据

        Returns:
            提取的元数据字典
        """
        import json
        from utils.common import get_corrected_path
        from config import Config

        metadata = {}

        # 从 file_record 提取
        if file_record:
            metadata['file_name'] = file_record.get('original_name', '')

            # 解析 meta_info
            if file_record.get('meta_info'):
                try:
                    meta_info = json.loads(file_record['meta_info'])
                    metadata.update(meta_info)
                except (json.JSONDecodeError, TypeError):
                    pass

        # 从 form_data 提取（会覆盖 file_record 中的同名字段）
        if form_data:
            # 常用字段映射
            field_mapping = {
                'course_name': ['course_name', 'course', '课程名称'],
                'class_name': ['class_name', 'class', '班级名称'],
                'semester': ['academic_year_semester', 'semester', '学年学期'],
                'teacher': ['teacher', 'teacher_name', '任课教师'],
                'course_code': ['course_code', 'course_no', '课程代码'],
            }

            for target_key, source_keys in field_mapping.items():
                for source_key in source_keys:
                    if source_key in form_data and form_data[source_key]:
                        metadata[target_key] = str(form_data[source_key]).strip()
                        break

        return metadata

    @staticmethod
    def generate_from_template(
        template_name: str,
        metadata: Dict[str, str],
        clean: bool = True
    ) -> str:
        """
        使用模板生成文件名

        Args:
            template_name: 模板名称（见 TEMPLATES）
            metadata: 元数据字典
            clean: 是否清理非法字符

        Returns:
            生成的文件名
        """
        template = FilenameGenerator.TEMPLATES.get(template_name, '{course_name}_{class_name}_成绩单.xlsx')

        # 确定文件扩展名
        if 'excel' in template_name:
            ext = 'xlsx'
        else:
            ext = 'docx'

        # 准备默认值（过滤空字符串）
        semester = metadata.get('semester', '').strip()
        course_name = metadata.get('course_name', '课程').strip()
        class_name = metadata.get('class_name', '班级').strip()

        # 如果课程名或班级为空，使用默认值
        if not course_name:
            course_name = '课程'
        if not class_name:
            class_name = '班级'

        # 填充模板（使用 .format() 而不是字符串拼接）
        try:
            # 对于包含 semester 的模板，如果 semester 为空，则移除相关部分
            if semester and '{semester}' in template:
                filename = template.format(
                    semester=semester,
                    course_name=course_name,
                    class_name=class_name
                )
            elif '{semester}' in template:
                # semester 为空，使用不含 semester 的模板
                template_without_semester = template.replace('{semester}', '').replace('《', '').replace('》', '').replace('--', '-')
                filename = template_without_semester.format(
                    course_name=course_name,
                    class_name=class_name
                )
                # 添加扩展名
                if not filename.endswith(f'.{ext}'):
                    filename = f"{filename}.{ext}"
            else:
                filename = template.format(
                    course_name=course_name,
                    class_name=class_name
                )
        except (KeyError, ValueError) as e:
            # 如果模板字段缺失，使用简单的后备方案
            filename = f"{course_name}_{class_name}_考核登分表.{ext}"

        # 清理非法字符
        if clean:
            filename = FilenameGenerator.clean_filename(filename)

        return filename

    @staticmethod
    async def generate_with_ai(
        metadata: Dict[str, str],
        file_type: str = 'xlsx',  # xlsx 或 docx
        doc_type: str = 'score_sheet'  # score_sheet 或 general
    ) -> Tuple[str, bool]:
        """
        使用 AI 生成智能文件名

        Args:
            metadata: 元数据字典
            file_type: 文件类型 (xlsx/docx)
            doc_type: 文档类型 (score_sheet/general)

        Returns:
            (文件名, 是否使用AI)
        """
        import httpx

        # 构建 AI 请求的提示词
        prompt = f"""请根据以下信息生成一个合适的文件名：

**文件类型**: {file_type} ({'Excel表格' if file_type == 'xlsx' else 'Word文档'})
**文档类型**: {'考核登分表' if doc_type == 'score_sheet' else '成绩单'}

**可用信息**:
- 学年学期: {metadata.get('semester', '未提供')}
- 课程名称: {metadata.get('course_name', '未提供')}
- 课程代码: {metadata.get('course_code', '未提供')}
- 班级名称: {metadata.get('class_name', '未提供')}
- 任课教师: {metadata.get('teacher', '未提供')}

**要求**:
1. 必须包含序号前缀（如 1. 或 8.），根据已知信息合理推测或使用默认值。
2. 严格遵循格式：序号. 学年学期《课程名称》文档类型-班级名称.扩展名
3. 示例："8. 2025-2026-1《服务器配置与管理》考核登分表-软工2406班（专升本）.xlsx"
4. 不要使用特殊字符（< > : " / \\ | ? *）
5. 只返回文件名，不要其他解释文字
6. 确保文件名清晰、完整、规范"""

        try:
            # 调用 AI 助手
            endpoint = "http://127.0.0.1:9011/api/ai/chat"
            payload = {
                "system_prompt": "你是一个文件命名专家，擅长生成规范、清晰的文件名。",
                "messages": [{"role": "user", "content": prompt}],
                "model_capability": "standard"
            }

            response = httpx.post(endpoint, json=payload, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                ai_filename = data.get("response_text", "").strip()

                # 清理 AI 返回的内容（可能包含 markdown 代码块标记）
                ai_filename = re.sub(r'```\w*\n?', '', ai_filename)
                ai_filename = ai_filename.strip()

                # 确保 AI 返回的文件名有正确的扩展名
                if not ai_filename.endswith(f'.{file_type}'):
                    ai_filename = f"{ai_filename}.{file_type}"

                # 清理非法字符
                ai_filename = FilenameGenerator.clean_filename(ai_filename)

                return ai_filename, True
            else:
                print(f"[FilenameGenerator] AI 调用失败: {response.status_code}")
                return FilenameGenerator.generate_from_template(
                    f'excel_{doc_type}' if file_type == 'xlsx' else 'word',
                    metadata
                ), False

        except Exception as e:
            print(f"[FilenameGenerator] AI 生成异常: {e}")
            return FilenameGenerator.generate_from_template(
                f'excel_{doc_type}' if file_type == 'xlsx' else 'word',
                metadata
            ), False

    @staticmethod
    def prepare_download_name(filename: str) -> str:
        """
        准备用于 HTTP 响应头的下载文件名

        Args:
            filename: 原始文件名

        Returns:
            适合 HTTP 响应头的文件名（中文会被 URL 编码）
        """
        try:
            # 尝试编码，如果不报错说明是纯 ASCII，不需要 quote
            filename.encode('latin-1')
            return filename
        except UnicodeEncodeError:
            # 包含中文，使用 URL 编码
            return quote(filename)


def get_export_filename(
    file_record: Dict = None,
    form_data: Dict = None,
    class_info: Dict = None,
    file_type: str = 'xlsx',
    use_ai: bool = False,
    doc_type: str = 'score_sheet'
) -> Tuple[str, str]:
    """
    获取导出文件的完整文件名

    Args:
        file_record: 文件记录（从数据库）
        form_data: 表单数据
        class_info: 班级信息（包含 name 和 course 字段）
        file_type: 文件类型 (xlsx/docx)
        use_ai: 是否使用 AI 生成
        doc_type: 文档类型 (score_sheet/general)

    Returns:
        (本地文件名, 下载文件名)

    Example:
        >>> filename, download_name = get_export_filename(
        ...     class_info={'name': '软工2406班', 'course': '服务器配置与管理'},
        ...     file_type='xlsx',
        ...     doc_type='score_sheet'
        ... )
        >>> print(filename)
        '服务器配置与管理_软工2406班_考核登分表.xlsx'
        >>> print(download_name)
        '服务器配置与管理_%E8%BD%AF%E5%B7%A52406%E7%8F%AD_%E8%80%83%E6%A0%B8%E7%99%BB%E7%99%BB%E5%88%86%E8%A1%A8.xlsx'
    """
    # 提取元数据
    metadata = FilenameGenerator.extract_metadata(file_record, form_data)

    # === [修复] 正确映射 class_info 字段 ===
    # class_info 的字段名是 name 和 course，需要映射到 class_name 和 course_name
    if class_info:
        # 优先使用 class_name 和 course_name（如果存在）
        if 'class_name' not in metadata or not metadata['class_name']:
            metadata['class_name'] = class_info.get('name', class_info.get('class_name', '班级'))

        if 'course_name' not in metadata or not metadata['course_name']:
            metadata['course_name'] = class_info.get('course', class_info.get('course_name', '课程'))

    # 生成文件名
    if use_ai:
        # 使用 AI 生成（需要异步调用）
        import asyncio
        try:
            filename, used_ai = asyncio.run(FilenameGenerator.generate_with_ai(
                metadata, file_type, doc_type
            ))
        except:
            # AI 失败，回退到模板
            filename = FilenameGenerator.generate_from_template(
                f'excel_{doc_type}' if file_type == 'xlsx' else 'word',
                metadata
            )
    else:
        # 使用模板生成
        template_key = f'excel_{doc_type}' if file_type == 'xlsx' else 'word'
        filename = FilenameGenerator.generate_from_template(template_key, metadata)

    # 准备下载文件名
    download_name = FilenameGenerator.prepare_download_name(filename)

    return filename, download_name
