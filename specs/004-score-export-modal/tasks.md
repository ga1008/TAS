# Tasks: 成绩导出选择弹窗

**Input**: Design documents from `/specs/004-score-export-modal/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Not explicitly requested - manual testing via quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No setup required - project already exists

本功能在现有项目基础上开发，无需额外的项目初始化。直接进入实现阶段。

**Checkpoint**: Setup complete (N/A - existing project)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 验证现有服务可用性，无需新建基础设施

- [x] T001 Verify ScoreDocumentService exists and works in `services/score_document_service.py`
- [x] T002 Verify existing Excel export endpoint works at `blueprints/grading.py:export_excel`

**Checkpoint**: Foundation ready - all existing services verified

---

## Phase 3: User Story 1 - 弹窗选择导出方式 (Priority: P1) 🎯 MVP

**Goal**: 实现导出选择弹窗的UI组件和交互逻辑

**Independent Test**: 点击"导出成绩"按钮 → 弹窗打开 → 可选择两种导出方式 → 可关闭弹窗

### Implementation for User Story 1

- [x] T003 [P] [US1] Create export choice modal component in `templates/components/export_choice_modal.html`
- [x] T004 [US1] Modify export button to trigger modal in `templates/grading.html:62-64`
- [x] T005 [US1] Add modal include statement to `templates/grading.html` (bottom of file)
- [x] T006 [US1] Implement modal open/close JavaScript logic in `templates/components/export_choice_modal.html`
- [x] T007 [US1] Implement card selection state toggle in `templates/components/export_choice_modal.html`
- [x] T008 [US1] Add loading state and button disable during export in `templates/components/export_choice_modal.html`

**Checkpoint**: At this point, User Story 1 should be fully functional - modal opens, cards selectable, can close

---

## Phase 4: User Story 2 - 导出到文档库 (Priority: P1)

**Goal**: 实现导出到文档库的后端API和前端调用

**Independent Test**: 选择"文档库"并确认 → API调用成功 → 文档库出现新文档

### Implementation for User Story 2

- [x] T009 [US2] Add API endpoint `POST /api/export_to_library/<class_id>` in `blueprints/grading.py`
- [x] T010 [US2] Implement authorization check (class owner only) in `blueprints/grading.py`
- [x] T011 [US2] Call ScoreDocumentService.generate_from_class() in `blueprints/grading.py`
- [x] T012 [US2] Handle no-grades-data edge case with proper error response in `blueprints/grading.py`
- [x] T013 [US2] Add fetch call to export_to_library API in `templates/components/export_choice_modal.html`
- [x] T014 [US2] Display success message and auto-close modal on success in `templates/components/export_choice_modal.html`
- [x] T015 [US2] Display error message with shake animation on failure in `templates/components/export_choice_modal.html`

**Checkpoint**: At this point, User Story 2 should be fully functional - export to library works end-to-end

---

## Phase 5: User Story 3 - 直接导出Excel (Priority: P2)

**Goal**: 将现有Excel导出功能集成到弹窗中

**Independent Test**: 选择"Excel表格"并确认 → 浏览器下载Excel文件

### Implementation for User Story 3

- [x] T016 [US3] Implement Excel export redirect on confirmation in `templates/components/export_choice_modal.html`
- [x] T017 [US3] Pass class_id to modal for Excel export URL construction in `templates/grading.html`

**Checkpoint**: At this point, User Story 3 should be fully functional - Excel export via modal works

---

## Phase 6: User Story 4 - Excel导出模板与文档库对接 (Priority: P2)

**Goal**: 验证机试考核登分表模板能正确从成绩文档获取数据

**Independent Test**: 从文档库选择成绩文档 → 使用机试考核登分表导出 → Excel数据正确

### Implementation for User Story 4

- [x] T018 [US4] Verify source_class_id is saved in meta_info by ScoreDocumentService in `services/score_document_service.py`
- [x] T019 [US4] Verify MachineTestScoreExporter reads source_class_id from meta_info in `export_core/templates/guangwai_machinetest_score.py`
- [ ] T020 [US4] Test end-to-end: export to library → export Excel from library document

**Checkpoint**: At this point, User Story 4 should be fully functional - data chain is complete

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final integration and validation

- [ ] T021 Run quickstart.md validation checklist
- [ ] T022 Test edge case: no graded students → should show error message
- [ ] T023 Test edge case: duplicate export → should add timestamp suffix to filename
- [ ] T024 Test modal close behaviors: X button, click outside, ESC key
- [ ] T025 Verify existing grading functionality unchanged (regression test)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies - verify existing services
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 3 (modal exists) + Phase 2 (service verified)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (modal exists)
- **User Story 4 (Phase 6)**: Depends on Phase 4 (export to library works)
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation only - modal UI is independent
- **User Story 2 (P1)**: Requires US1 (modal exists to trigger export)
- **User Story 3 (P2)**: Requires US1 (modal exists for Excel option)
- **User Story 4 (P2)**: Requires US2 (documents must exist in library first)

### Within Each User Story

- Modal component before integration tasks
- Backend API before frontend calling code
- Core implementation before edge case handling

### Parallel Opportunities

- T003 (modal component) can start immediately after T001-T002 verification
- T016-T017 (US3) can run in parallel with T009-T015 (US2) after T003-T008 (US1) complete
- T018-T019 (US4 verification) are read-only and can run in parallel

---

## Parallel Example: User Story 1

```bash
# After Phase 2 verification, launch these in parallel:
Task: "Create export choice modal component in templates/components/export_choice_modal.html"

# After modal component created, these tasks are sequential within the same file:
Task: "Add modal include statement to templates/grading.html"
Task: "Modify export button to trigger modal in templates/grading.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 2: Verify existing services
2. Complete Phase 3: User Story 1 (modal UI)
3. Complete Phase 4: User Story 2 (export to library API)
4. **STOP and VALIDATE**: Test modal + library export independently
5. This gives core value: teachers can export scores to document library

### Incremental Delivery

1. MVP (US1 + US2) → Test independently → Deploy
2. Add US3 (Excel integration) → Test → Deploy
3. Add US4 (template verification) → Test → Deploy
4. Polish phase → Final validation

### File Change Summary

| File | Changes |
|------|--------|
| `templates/grading.html` | Modify export button, add modal include |
| `templates/components/export_choice_modal.html` | [NEW] Modal component |
| `blueprints/grading.py` | Add export_to_library API endpoint |
| `services/score_document_service.py` | Verify only (no changes expected) |
| `export_core/templates/guangwai_machinetest_score.py` | Verify only (no changes expected) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing ScoreDocumentService and Excel export logic should NOT be modified
