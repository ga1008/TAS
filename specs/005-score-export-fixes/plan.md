# Implementation Plan: 成绩导出与考核登分表完善

**Branch**: `005-score-export-fixes` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-score-export-fixes/spec.md`

## Summary

修复成绩导出功能的两个核心问题：(1) 导出时仅保留大题分数，不包含小题；(2) Excel 导出使用动态题目分值表单。同时新增"考核登分表"文档分类，提供专属详情页面支持成绩查看、编辑和 Excel 导出。

## Technical Context

**Language/Version**: Python 3.x + Flask 2.x + Jinja2
**Primary Dependencies**: Flask, SQLite3, openpyxl, httpx
**Storage**: SQLite (`data/grading_system_v2.db`)
**Testing**: 手动功能测试 + Python 脚本验证
**Target Platform**: Linux/Windows 服务器 (端口 5010/9011)
**Project Type**: Web 应用 (Flask + Jinja2 模板)
**Performance Goals**: 成绩导出 < 3 秒 (100 学生规模)
**Constraints**: 不破坏现有批改流程和文档库功能
**Scale/Scope**: 单机部署，50-200 学生/班级

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **模块化解耦**: 新增 `is_main_question()` 和 `aggregate_main_questions()` 作为独立工具函数
- [x] **微服务分离**: 不涉及 AI 微服务，纯后端逻辑在主应用实现
- [x] **前端设计一致性**: 新选项卡和详情页遵循 `FRONTEND_GUIDE.md` 规范
- [x] **批改器可扩展性**: 不涉及批改器修改
- [x] **数据库迁移友好**: 仅扩展 doc_category 合法值，无表结构变更
- [x] **AI 能力分层**: 不涉及 AI 调用
- [x] **AI 内容生成与缓存**: 不涉及 AI 内容生成
- [x] **前端 AI 内容展示**: 不涉及 AI 内容展示
- [x] **AI 提示工程**: 不涉及 AI 提示词
- [x] **个性化AI交互**: 不涉及 AI 交互

## Project Structure

### Documentation (this feature)

```text
specs/005-score-export-fixes/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output - Technology decisions
├── data-model.md        # Phase 1 output - Entity definitions
├── quickstart.md        # Phase 1 output - Validation steps
├── contracts/
│   └── internal.md      # Phase 1 output - API contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (to be created by /speckit.tasks)
```

### Source Code (repository root)

```text
services/
└── score_document_service.py  # 修改: 大题过滤、新元数据字段

export_core/
├── doc_config.py              # 修改: 新增 score_sheet 类型
└── templates/
    └── guangwai_machinetest_score.py  # 修改: 支持动态字段

blueprints/
├── library.py                 # 修改: 新增 API 端点
└── export.py                  # 修改: 动态导出配置 API

templates/
└── library/
    └── index.html             # 修改: 新增选项卡、详情页增强
```

**Structure Decision**: 使用现有 Flask 单体架构，在相应模块中进行增量修改。

## Implementation Phases

### Phase 1: 核心逻辑 (P1 功能)

1. **services/score_document_service.py**
   - 新增 `is_main_question()` 函数
   - 新增 `aggregate_main_questions()` 函数
   - 修改 `build_metadata()` 添加 question_scores 和 total_max_score
   - 修改 `build_markdown_content()` 过滤小题列
   - 修改 `generate_from_class()` 使用 doc_category='score_sheet'

2. **export_core/doc_config.py**
   - 添加 `score_sheet` 到 `TYPES` 字典
   - 添加 `score_sheet` 到 `FIELD_SCHEMAS`

### Phase 2: 前端集成 (P1 功能)

3. **templates/library/index.html**
   - 在 categoryTabs 中添加"8. 考核登分表"选项卡
   - 调整选项卡顺序

4. **blueprints/export.py**
   - 新增 `/api/export/score_sheet/<asset_id>/config` API
   - 返回动态字段配置

5. **前端 Excel 导出表单**
   - 根据 question_scores 动态生成输入字段
   - 预填 max_score 值

### Phase 3: 详情页增强 (P2 功能)

6. **成绩编辑功能**
   - 新增 `/api/update_score_cell` API
   - 前端可编辑单元格组件
   - 总分自动计算

7. **导出按钮图标**
   - 使用 fa-file-excel 图标

### Phase 4: 回归测试

8. **验证现有功能**
   - 批改流程
   - 其他文档类型操作
   - 旧成绩文档可访问性

## Complexity Tracking

> 无宪法违规，无需记录复杂度追踪。

## Related Documents

- [spec.md](./spec.md) - Feature specification
- [research.md](./research.md) - Technology decisions
- [data-model.md](./data-model.md) - Entity definitions
- [contracts/internal.md](./contracts/internal.md) - API contracts
- [quickstart.md](./quickstart.md) - Validation steps
