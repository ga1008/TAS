# Export Core Blueprint

## 1. 设计理念
导出系统旨在解决“从数据库数据生成复杂 Word 报表”的需求。它采用了 **Code-as-Configuration** 的方式，每个导出模板是一个 Python 类。

## 2. 组件结构

### TemplateManager (`export_core/manager.py`)
* 自动扫描 `export_core/templates/` 目录。
* 将模板类的元数据（特别是 `UI_SCHEMA`）同步到数据库 `export_templates` 表。
* **目的**: 前端通过读取数据库的 Schema 动态渲染表单，后端通过 ID 实例化模板类执行导出。

### BaseExportTemplate (`export_core/base_template.py`)
* 所有导出模板的基类。
* 必须定义 `UI_SCHEMA`: 一个描述所需参数的字典（用于前端生成输入框）。
* 必须实现 `run(self, params, output_path)`: 执行生成 docx 的逻辑。

## 3. 工作流
1.  **启动**: Manager 扫描 .py 文件 -> 更新 DB。
2.  **前端展示**: `/export` 页面读取 DB，根据 `ui_schema` 渲染表单。
3.  **执行**: 用户提交表单 -> 后端找到对应 Template 类 -> 调用 `run()` -> 返回生成的 Word 文件。