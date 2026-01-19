# Grading Core Blueprint

## 1. 架构概述
批改核心位于 `grading_core/`，采用 **策略模式 (Strategy Pattern)**。每个批改脚本（Grader）是一个独立的 Python 文件，负责特定的批改逻辑。

## 2. 核心组件

### BaseGrader (`grading_core/base.py`)
所有批改器必须继承此类。
* **职责**: 提供标准接口 `grade()` 和通用工具方法。
* **关键方法**:
    * `scan_files(root_dir)`: 建立文件名索引，解决大小写不敏感和深层路径查找问题。
    * `smart_find(target, alternatives, ...)`: 在索引中查找文件，支持别名和模糊匹配。
    * `verify_command(content, regex, ...)`: 基于正则的命令/代码检查引擎。
    * `read_text_content(path)`: 自动处理编码 (UTF-8/GBK)。

### GraderFactory (`grading_core/factory.py`)
* **职责**: 动态加载 `grading_core/graders/` 目录下的所有脚本。
* **特性**: 支持 **热重载 (Hot Reload)**。当 AI 生成新脚本或用户修改脚本后，无需重启服务器即可生效。

### GradingResult (`grading_core/base.py`)
* **职责**: 标准化批改结果，包含 `total_score`, `score_details` (JSON), `deduct_details`。

## 3. 开发/生成新 Grader 规范
AI 在生成新的 Grader 时，必须遵循以下模板：
1.  继承 `BaseGrader`。
2.  定义类属性 `ID` (唯一) 和 `NAME` (显示名)。
3.  实现 `grade(self, student_dir, student_info)` 方法。
4.  在 `grade` 方法首行调用 `self.scan_files(student_dir)`。
5.  使用 `self.smart_find` 查找文件，使用 `self.verify_command` 检查内容。
6.  返回 `GradingResult` 对象。