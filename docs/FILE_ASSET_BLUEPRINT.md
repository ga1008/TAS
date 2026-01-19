# File Asset Management Blueprint

## 1. 核心逻辑
为了避免重复文件占用存储和重复解析，系统实现了基于 **SHA256 哈希** 的文件去重机制。

## 2. 数据库实体: `file_assets`
* `file_hash`: 文件的唯一标识。
* `physical_path`: 文件在磁盘上的实际存储路径。
* `parsed_content`: AI 解析后的结构化内容（缓存）。
* `meta_info`: JSON 格式的元数据（如：{"academic_year": "2024-2025", "course": "Python"}）。

## 3. 业务流程 (`services/file_service.py`)
1.  **上传**: 计算文件 Hash -> 查库。
2.  **命中**: 如果 Hash 存在，直接返回现有的 file_id（秒传），不重复保存物理文件。
3.  **未命中**: 保存物理文件到磁盘 -> 写入 `file_assets` 表。
4.  **复用**: 多个业务（如 AI 生成、导出、学生导入）均通过 `file_id` 引用文件。

## 4. 解析与清洗
* 支持通过 `AiService` 对文件进行多模态解析（Vision/Text）。
* 解析结果会回写到 `file_assets`，供后续业务（如生成批改脚本）直接使用，无需重复调用 AI。