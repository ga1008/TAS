# Tasks: 自动评分结果同步到文档库

**Input**: Design documents from `specs/001-grading-library-sync/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Not included (project has no automated test framework - spec.md line 18: "手动集成测试")

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files and directory structure

- [X] T001 [P] Create utils/__init__.py (if not exists)
- [X] T002 [P] Create utils/academic_year.py with infer_academic_year_semester() function

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema changes and helper methods required by all user stories

**⚠️ CRITICAL**: User stories cannot begin until this phase is complete

- [X] T003 Add source_class_id column migration in database.py init_db_tables()
- [X] T004 [P] Add get_task_by_grader_id() method in database.py
- [X] T005 [P] Add get_file_asset_by_path() method in database.py
- [X] T006 [P] Add save_file_asset() method in database.py
- [X] T007 [P] Add count_score_documents_for_class() method in database.py

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - 批改完成自动生成成绩文档 (Priority: P1) 🎯 MVP

**Goal**: After batch grading completes, automatically generate a Markdown score document in the document library

**Independent Test**: Complete batch grading on a class with students, verify score document appears in document library with correct format and metadata

### Implementation for User Story 1

- [X] T008 [US1] Create services/score_document_service.py with class skeleton and imports
- [X] T009 [US1] Implement ScoreDocumentService.build_metadata() for metadata collection in services/score_document_service.py
- [X] T010 [US1] Implement ScoreDocumentService.build_markdown_content() for Markdown generation in services/score_document_service.py
- [X] T011 [US1] Implement ScoreDocumentService._generate_filename() for naming in services/score_document_service.py
- [X] T012 [US1] Implement ScoreDocumentService._resolve_filename_conflict() with timestamp suffix in services/score_document_service.py
- [X] T013 [US1] Implement ScoreDocumentService.generate_from_class() main entry point in services/score_document_service.py
- [X] T014 [US1] Add score document generation call in blueprints/grading.py run_batch_grading()
- [X] T015 [US1] Add error handling and logging for generation failures in blueprints/grading.py

**Checkpoint**: User Story 1 complete - batch grading auto-generates score documents

---

## Phase 4: User Story 2 - 成绩文档导出为机试考核登分表 (Priority: P2)

**Goal**: Export score documents to Excel using the "机试考核登分表" template with auto-filled data

**Independent Test**: Select a generated score document in document library, export with "机试考核登分表" template, verify Excel contains correct student scores

### Implementation for User Story 2

- [X] T016 [US2] Add source_class_id lookup logic in export_core/templates/guangwai_machinetest_score.py generate()
- [X] T017 [US2] Implement priority chain: source_class_id → class_name fuzzy match in export_core/templates/guangwai_machinetest_score.py
- [X] T018 [US2] Add auto_fill_key support for meta_info fields in export_core/templates/guangwai_machinetest_score.py UI_SCHEMA

**Checkpoint**: User Story 2 complete - score documents exportable to Excel

---

## Phase 5: User Story 3 - 元数据追溯与数据库优化 (Priority: P3)

**Goal**: Trace teacher and course_code from exam file metadata via ai_tasks linkage

**Independent Test**: Generate score document for a class with AI-generated grader, verify teacher name from exam metadata appears in document

### Implementation for User Story 3

- [X] T019 [US3] Implement metadata tracing logic: class.strategy → ai_tasks.grader_id → ai_tasks.exam_path in services/score_document_service.py build_metadata()
- [X] T020 [US3] Add file_assets lookup for exam file meta_info in services/score_document_service.py build_metadata()
- [X] T021 [US3] Extract teacher and course_code from exam meta_info JSON in services/score_document_service.py build_metadata()
- [X] T022 [US3] Add academic_year_semester fallback using infer_academic_year_semester() in services/score_document_service.py build_metadata()

**Checkpoint**: User Story 3 complete - metadata fully traced from exam files

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final integration and validation

- [X] T023 Run manual integration test: complete batch grading → verify score document → export Excel
- [X] T024 Verify edge cases: partial failures, missing metadata, multiple grading runs
- [X] T025 Verify existing grading functionality unchanged (regression check)
- [X] T026 Run quickstart.md testing checklist validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion (can run parallel to US1)
- **User Story 3 (Phase 5)**: Depends on User Story 1 (metadata tracing builds on US1 service)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

```
            ┌─────────────┐
            │   Setup     │
            │  (Phase 1)  │
            └──────┬──────┘
                   │
            ┌──────▼──────┐
            │ Foundational│
            │  (Phase 2)  │
            └──────┬──────┘
                   │
         ┌─────────┴─────────┐
         │                   │
  ┌──────▼──────┐     ┌──────▼──────┐
  │   US1 (P1)  │     │   US2 (P2)  │
  │  Auto-gen   │     │   Export    │
  └──────┬──────┘     └─────────────┘
         │
  ┌──────▼──────┐
  │   US3 (P3)  │
  │  Metadata   │
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │   Polish    │
  │  (Phase 6)  │
  └─────────────┘
```

### Parallel Opportunities

**Phase 1 (Setup)**:
```bash
# All tasks can run in parallel:
Task: T001 "Create utils/__init__.py"
Task: T002 "Create utils/academic_year.py"
```

**Phase 2 (Foundational)**:
```bash
# After T003 (migration), these can run in parallel:
Task: T004 "Add get_task_by_grader_id() method"
Task: T005 "Add get_file_asset_by_path() method"
Task: T006 "Add save_file_asset() method"
Task: T007 "Add count_score_documents_for_class() method"
```

**Phase 3-4 (User Stories 1 & 2)**:
```bash
# US2 can start while US1 is in progress (different files):
Task: T008-T015 (US1 in services/ and blueprints/grading.py)
Task: T016-T018 (US2 in export_core/templates/)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (2 tasks)
2. Complete Phase 2: Foundational (5 tasks)
3. Complete Phase 3: User Story 1 (8 tasks)
4. **STOP and VALIDATE**: Test batch grading → score document generation
5. Deploy/demo if ready (15 tasks total for MVP)

### Incremental Delivery

1. Setup + Foundational → Foundation ready (7 tasks)
2. Add User Story 1 → Test independently → **MVP Ready** (15 tasks)
3. Add User Story 2 → Test independently → Export feature ready (18 tasks)
4. Add User Story 3 → Test independently → Full metadata support (22 tasks)
5. Polish → Production ready (26 tasks)

---

## Notes

- [P] tasks = different files, no dependencies
- [US#] label maps task to specific user story for traceability
- Each user story independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No automated tests (manual testing per quickstart.md checklist)

## Files Modified Summary

| File | Change | User Story |
|------|--------|------------|
| `utils/__init__.py` | NEW | Setup |
| `utils/academic_year.py` | NEW | Setup |
| `database.py` | MODIFY | Foundational |
| `services/score_document_service.py` | NEW | US1, US3 |
| `blueprints/grading.py` | MODIFY | US1 |
| `export_core/templates/guangwai_machinetest_score.py` | MODIFY | US2 |
