# Tasks: 成绩导出与考核登分表完善

**Input**: Design documents from `/specs/005-score-export-fixes/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, contracts/internal.md ✅

**Tests**: Tests are NOT explicitly requested in the specification. Tasks focus on implementation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **This project**: Flask single project at repository root
- Services: `services/`
- Blueprints: `blueprints/`
- Templates: `templates/`
- Export Core: `export_core/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: New document type registration and utility functions

- [x] T001 [P] Add `score_sheet` type to TYPES dict in `export_core/doc_config.py`
- [x] T002 [P] Add `score_sheet` to FIELD_SCHEMAS in `export_core/doc_config.py`
- [x] T003 Add `is_main_question()` helper function in `services/score_document_service.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core aggregation logic that all P1 stories depend on

**⚠️ CRITICAL**: US1, US2, US3 depend on this phase's completion

- [x] T004 Implement `aggregate_main_questions()` function in `services/score_document_service.py` that filters and aggregates sub-question scores into main questions

**Checkpoint**: Aggregation logic ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 导出成绩时仅保留大题分数 (Priority: P1) 🎯 MVP

**Goal**: Export only main question scores (一、二、三), excluding sub-questions (1.1, 1.2), with metadata for max scores

**Independent Test**: 批改一个包含多道大题和小题的任务 → 导出到文档库 → 检查Markdown表格仅显示大题分数 → 检查元数据包含各大题满分和总分

### Implementation for User Story 1

- [x] T005 [US1] Modify `build_metadata()` in `services/score_document_service.py` to add `question_scores` array and `total_max_score` field
- [x] T006 [US1] Modify `build_markdown_content()` in `services/score_document_service.py` to filter sub-questions and only display main question columns
- [x] T007 [US1] Update `generate_from_class()` in `services/score_document_service.py` to use `doc_category='score_sheet'` instead of `'other'`

**Checkpoint**: Exported score documents now contain only main question columns with correct metadata

---

## Phase 4: User Story 2 - 动态题目分值配置表单 (Priority: P1)

**Goal**: Excel export form shows dynamic fields per main question instead of single text input

**Independent Test**: 打开一个含3道大题的成绩文档 → 点击导出Excel → 看到3个独立的分值输入框，预填各大题满分

### Implementation for User Story 2

- [x] T008 [US2] Add `/api/export/score_sheet/<asset_id>/config` endpoint in `blueprints/export.py` to return dynamic field configuration from meta_info.question_scores
- [x] T009 [US2] Update export modal JavaScript in `templates/library/index.html` to call config API and generate dynamic input fields for each main question
- [x] T010 [US2] Update export submission logic in `templates/library/index.html` to send individual question scores as array instead of comma-separated string
- [x] T011 [US2] Modify `MachineTestScoreExporter` in `export_core/templates/guangwai_machinetest_score.py` to accept dynamic question scores array

**Checkpoint**: Excel export now shows dynamic form fields based on document metadata

---

## Phase 5: User Story 3 - 新增"考核登分表"文档分类 (Priority: P1)

**Goal**: Add `score_sheet` category tab in document library, positioned before "期末试卷"

**Independent Test**: 导出一份成绩到文档库 → 在文档库选项卡中看到"8. 考核登分表" → 该文档出现在此分类下

### Implementation for User Story 3

- [x] T012 [US3] Add `score_sheet` tab button in categoryTabs section of `templates/library/index.html` with label "8. 考核登分表" positioned between "3. 评分细则" and "9. 期末试卷"
- [x] T013 [US3] Update `window.docTypes` JavaScript object in `templates/library/index.html` to include `score_sheet: '考核登分表'`
- [x] T014 [US3] Update `getIcon()` JavaScript function in `templates/library/index.html` to return appropriate icon for `score_sheet` category (fa-table or fa-file-excel)

**Checkpoint**: Document library now shows score_sheet category tab and filters correctly

---

## Phase 6: User Story 4 - 考核登分表详情页面 (Priority: P2)

**Goal**: Score sheet documents have dedicated detail view with editable scores and Excel export button

**Independent Test**: 打开一个考核登分表文档 → 能看到学生成绩表格 → 能编辑某学生分数 → 能点击Excel图标导出

### Implementation for User Story 4

- [x] T015 [US4] Add `/api/update_score_cell` endpoint in `blueprints/library.py` to update individual student scores and recalculate total
- [x] T016 [US4] Add score sheet detail view mode in `templates/library/index.html` that displays student grades in an editable table when doc_category is 'score_sheet'
- [x] T017 [US4] Implement editable table cell functionality in `templates/library/index.html` with click-to-edit and auto-save on blur
- [x] T018 [US4] Add total score auto-recalculation logic in frontend when any main question score is edited
- [x] T019 [US4] Update export button to display fa-file-excel icon in `templates/library/index.html` for score_sheet documents

**Checkpoint**: Score sheet detail page is fully functional with editing and export capabilities

---

## Phase 7: User Story 5 - 系统功能完整性保障 (Priority: P2)

**Goal**: All changes do not break existing functionality

**Independent Test**: 完成所有改动后 → 执行批改流程 → 查看其他类型文档 → 确认功能正常

### Implementation for User Story 5

- [x] T020 [US5] Verify old score documents (doc_category='other') remain accessible in "其他" category
- [ ] T021 (⚡ manual) [US5] Test complete grading workflow: create task → grade submissions → export to document library
- [ ] T022 (⚡ manual) [US5] Test other document types (exam, standard, syllabus, plan) view and edit functionality
- [ ] T023 (⚡ manual) [US5] Test existing Excel export functionality with non-score_sheet documents

**Checkpoint**: All regression tests pass, existing functionality intact

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T024 (⚡ manual) Run quickstart.md validation scenarios manually
- [x] T025 Verify edge case handling: documents without question_scores metadata fall back gracefully
- [x] T026 Verify edge case handling: student scores with null/undefined values display as "-"

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on T003 from Setup (is_main_question function)
- **User Story 1 (Phase 3)**: Depends on T004 (aggregate_main_questions)
- **User Story 2 (Phase 4)**: Depends on US1 completion (needs question_scores in metadata)
- **User Story 3 (Phase 5)**: Depends on T001, T002 (doc_config registration)
- **User Story 4 (Phase 6)**: Depends on US1 and US3 completion
- **User Story 5 (Phase 7)**: Depends on all other user stories
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

```
Setup (T001-T003)
       ↓
Foundational (T004)
       ↓
   ┌───┴───┐
   ↓       ↓
  US1     US3
 (T005-   (T012-
  T007)   T014)
   ↓       ↓
  US2     ↓
 (T008-   ↓
  T011)   ↓
   ↓       ↓
   └───┬───┘
       ↓
      US4
   (T015-T019)
       ↓
      US5
   (T020-T023)
       ↓
     Polish
   (T024-T026)
```

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (both in doc_config.py but different dicts)
- **Phase 3+4 vs Phase 5**: After Foundational, US1+US2 can run in parallel with US3 (different files)
- **Within US3**: T012, T013, T014 all modify same file - must be sequential
- **Within US4**: T015 (backend) can run in parallel with T019 (frontend icon change)

---

## Parallel Example: Phase 1 Setup

```bash
# Launch setup tasks in parallel (different config entries):
Task T001: "Add score_sheet to TYPES dict in export_core/doc_config.py"
Task T002: "Add score_sheet to FIELD_SCHEMAS in export_core/doc_config.py"
```

---

## Parallel Example: US1/US2 vs US3

```bash
# After Foundational phase, these tracks can run in parallel:

# Track A: Core export logic (US1 → US2)
Task T005-T007: User Story 1 implementation
Task T008-T011: User Story 2 implementation (after US1)

# Track B: Frontend category tab (US3)
Task T012-T014: User Story 3 implementation
```

---

## Implementation Strategy

### MVP First (User Story 1 + 3 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004)
3. Complete Phase 3: User Story 1 (T005-T007) - Core export fix
4. Complete Phase 5: User Story 3 (T012-T014) - Category tab
5. **STOP and VALIDATE**: Test exported documents have correct structure and appear in score_sheet category
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 + US3 → Core functionality (MVP!)
3. Add US2 → Dynamic export form enhancement
4. Add US4 → Detail page with editing
5. Add US5 → Full regression validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Primary files modified: `services/score_document_service.py`, `export_core/doc_config.py`, `templates/library/index.html`, `blueprints/export.py`, `blueprints/library.py`
- No database schema changes required
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
