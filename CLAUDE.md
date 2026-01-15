# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

基于 AI 的自动化作业批改系统，面向教育工作者。使用 Python/Flask 后端和 Jinja2 模板。通过 AI 模型（OpenAI 兼容协议、火山引擎）自动生成 Python 批改脚本来评估学生提交的作业。

## 开发命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动主 Flask 应用 (端口 5010)
python app.py

# 启动 AI 助手微服务 (端口 9011) - AI 功能必需
python ai_assistant.py

# Docker 部署
docker-compose up
```

## 架构

### 双服务架构
- **主应用** (`app.py`, 端口 5010): Flask Web 应用，负责 UI、批改调度、班级/学生管理
- **AI 助手** (`ai_assistant.py`, 端口 9011): 独立微服务，处理 AI 操作（多厂商抽象层）

### 核心组件

**蓝图** (`blueprints/`):
- `admin.py` - 管理员认证、AI 厂商/模型配置
- `grading.py` - 作业提交、批改执行
- `ai_generator.py` - AI 驱动的批改脚本生成
- `library.py` - 文档/文件库
- `export.py` - 成绩导出 (Excel)
- `signatures.py` - 电子签名
- `auth.py`, `main.py` - 用户认证、首页

**批改框架** (`grading_core/`):
- `base.py` - `BaseGrader` 抽象基类和 `GradingResult` - 所有批改器必须继承 `BaseGrader`
- `factory.py` - `GraderFactory` 支持热重载（脚本更新无需重启服务）
- `graders/` - AI 自动生成的 Python 批改脚本存放目录

**服务层** (`services/`):
- `ai_service.py` - 文档解析（视觉模式 → 文本模式 → 降级处理）
- `file_service.py` - 文件处理
- `grading_service.py` - 批改执行

**AI 工具** (`ai_utils/`):
- `ai_helper.py` - 统一的 AI 平台抽象层（OpenAI、火山引擎）
- `ai_concurrency_manager.py` - 并发请求管理
- `volc_file_manager.py` - 火山引擎文件上传

### 数据流程
1. 管理员通过 `/admin` 配置 AI 厂商/模型
2. 教师上传试卷 + 评分标准 → AI 生成 Python 批改脚本 → 保存至 `grading_core/graders/`
3. 教师创建班级，上传学生名单
4. 学生提交作业（自动解压 zip/rar）
5. 系统对每份提交运行批改脚本
6. 导出成绩至 Excel

### 关键配置 (`config.py`)
- `AI_ASSISTANT_BASE_URL`: AI 服务端点（默认: `http://127.0.0.1:9011`）
- `DB_PATH`: SQLite 数据库（`data/grading_system_v2.db`）
- `GRADERS_DIR`: 批改脚本存放目录
- `ADMIN_USERNAME`/`ADMIN_PASSWORD`: 默认 `admin`/`admin123`（可通过环境变量配置）

### 编写自定义批改器

批改器继承 `BaseGrader` 并实现 `grade(student_dir, student_info) -> GradingResult`。

内置工具方法（请直接调用，勿重复实现）:
- `self.scan_files(root_dir)` - 构建学生提交文件的索引
- `self.smart_find(filename, alternatives, ignore_subfixes)` - 模糊匹配查找文件
- `self.read_text_content(file_path)` - 自动检测编码读取文件
- `self.verify_command(content, result, strict_regex, loose_regex, pts, name)` - 基于正则的验证

结果记录:
- `self.res.add_sub_score(name, score)` - 记录某题得分
- `self.res.add_deduction(msg)` - 记录扣分原因
- `self.res.total_score` - 总分（必须计算赋值）
