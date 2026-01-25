# Implementation Plan: 自动评分结果同步到文档库

**Branch**: `001-grading-library-sync` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-grading-library-sync/spec.md`

## Summary

批量批改完成后，系统自动从批改核心、班级、成绩表收集元数据和学生分数，生成 Markdown 格式的成绩文档存入文档库（file_assets 表）。同时增强"机试考核登分表" Excel 导出功能，支持从成绩文档自动填充数据。核心实现涉及：
1. 在 `services/grading_service.py` 中添加成绩文档生成逻辑
2. 增强 `export_core/templates/guangwai_machinetest_score.py` 支持从成绩文档获取数据
3. 添加元数据追溯逻辑，从 ai_tasks → file_assets 获取教师和课程编码

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: Flask, SQLite, openpyxl
**Storage**: SQLite (data/grading_system_v2.db) - file_assets, grades, ai_tasks, classes 表
**Testing**: 手动集成测试（项目无自动化测试框架）
**Target Platform**: Linux/Windows 服务器
**Project Type**: Web 应用 (Flask + Jinja2)
**Performance Goals**: 成绩文档生成 < 5秒（SC-001）
**Constraints**: 同步操作，不阻塞批改流程响应
**Scale/Scope**: 单班级 50-100 学生，每次批改生成一份文档

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **模块化解耦**: 成绩文档生成逻辑封装在 services 层，不引入新的循环依赖
- [x] **微服务分离**: 不涉及 AI 调用，无需与 AI 助手微服务交互
- [x] **前端设计一致性**: 无新增前端页面，仅增强现有导出功能
- [x] **批改器可扩展性**: 不修改 BaseGrader，仅读取批改结果
- [x] **数据库迁移友好**: 如需新增字段使用 `_migrate_table` 迁移
- [x] **AI 能力分层**: 不涉及 AI 调用
- [x] **AI 内容生成与缓存**: 不涉及 AI 生成内容
- [x] **前端 AI 内容展示**: 不涉及 AI 前端展示
- [x] **AI 提示工程**: 不涉及 AI 提示词
- [x] **个性化AI交互**: 不涉及 AI 交互

## Project Structure

### Documentation (this feature)

```text
specs/001-grading-library-sync/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal Python interfaces)
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
autoCorrecting/
├── services/
│   ├── grading_service.py        # [MODIFY] 添加成绩文档生成逻辑
│   └── score_document_service.py # [NEW] 成绩文档生成服务（可选独立模块）
├── blueprints/
│   └── grading.py                # [MODIFY] 批改完成后调用文档生成
├── export_core/
│   └── templates/
│       └── guangwai_machinetest_score.py  # [MODIFY] 增强数据源逻辑
├── database.py                   # [MODIFY] 添加元数据追溯查询方法
└── utils/
    └── academic_year.py          # [NEW] 学年学期推断工具函数
```

**Structure Decision**: 遵循现有项目结构，核心逻辑放在 `services/` 层，通过 `blueprints/grading.py` 触发调用。考虑到功能独立性，可将成绩文档生成封装为独立服务模块 `score_document_service.py`。

## Phase 1 Deliverables

*Completed 2026-01-26*

- [x] [research.md](./research.md) - Integration points, DB schema, metadata tracing
- [x] [data-model.md](./data-model.md) - Schema changes, entity definitions, queries
- [x] [contracts/internal.md](./contracts/internal.md) - Service interfaces
- [x] [quickstart.md](./quickstart.md) - Step-by-step implementation guide

## Complexity Tracking

> No violations. All changes comply with constitution principles.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |

## Next Steps

Run `/speckit.tasks` to generate implementation tasks from this plan.
