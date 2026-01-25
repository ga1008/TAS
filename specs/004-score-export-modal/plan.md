# Implementation Plan: 成绩导出选择弹窗

**Branch**: `004-score-export-modal` | **Date**: 2026-01-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-score-export-modal/spec.md`

## Summary

实现成绩导出选择弹窗功能：当用户点击"导出成绩"按钮时，系统弹出选择弹窗，提供两种导出方式：
1. **导出到文档库**：收集元数据并生成Markdown格式的成绩文档，存入file_assets表
2. **直接导出Excel**：保持原有的Excel下载功能

技术方案：复用现有的 `ScoreDocumentService` 服务，参考 `jwxt_login_modal.html` 的弹窗设计模式，新增前端弹窗组件和后端API端点。

## Technical Context

**Language/Version**: Python 3.9+, JavaScript ES6+
**Primary Dependencies**: Flask 2.x, Jinja2, Tailwind CSS, FontAwesome 6
**Storage**: SQLite (file_assets, classes, grades, ai_tasks 表)
**Testing**: 手动集成测试
**Target Platform**: Web Browser (Chrome, Firefox, Edge)
**Project Type**: Web application (Flask + Jinja2 templates)
**Performance Goals**: 弹窗打开 < 200ms, 导出操作 < 5s
**Constraints**: 遵循现有UI设计规范 (FRONTEND_GUIDE.md)
**Scale/Scope**: 单用户操作，每次导出约 30-100 学生数据

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **模块化解耦**: 新增API端点在 `blueprints/grading.py`，服务逻辑在 `services/score_document_service.py`
- [x] **微服务分离**: 不涉及AI服务调用，纯本地操作
- [x] **前端设计一致性**: 弹窗设计参考 `jwxt_login_modal.html`，遵循 FRONTEND_GUIDE.md
- [x] **批改器可扩展性**: 不涉及批改器修改
- [x] **数据库迁移友好**: 不需要新增数据库字段（复用现有 file_assets 表）
- [x] **AI 能力分层**: 不涉及AI调用
- [x] **AI 内容生成与缓存**: 不涉及AI内容
- [x] **前端 AI 内容展示**: 不涉及AI内容
- [x] **AI 提示工程**: 不涉及AI提示词
- [x] **个性化AI交互**: 不涉及AI交互

## Project Structure

### Documentation (this feature)

```text
specs/004-score-export-modal/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
# 修改的文件
templates/
├── grading.html                      # 添加弹窗组件和触发逻辑
└── components/
    └── export_choice_modal.html      # [NEW] 导出选择弹窗组件

blueprints/
└── grading.py                        # 添加导出到文档库的API端点

services/
└── score_document_service.py         # 已存在，复用generate_from_class方法
```

**Structure Decision**: 采用组件化方式，新建独立的弹窗组件文件 `export_choice_modal.html`，通过 Jinja2 include 嵌入到 `grading.html`。后端API新增在现有的 `grading.py` 蓝图中，保持路由一致性。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

无违规项，不需要填写。
