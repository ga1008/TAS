# Implementation Tasks: Grading Core Creation and Task Selection Improvements

**Feature Branch**: `001-grading-core-creation`
**Date**: 2026-02-05
**Status**: Ready for Implementation

---

## Overview

This document contains actionable, dependency-ordered tasks for implementing the grading core creation and task selection improvements. Tasks are organized by user story to enable independent implementation and testing.

**Total Tasks**: 27
**Estimated Complexity**: Medium
**MVP Scope**: Phase 3 (User Story 1) + Phase 4 (User Story 3)

---

## Task Format Legend

- `- [ ]` = Checkbox (click to complete)
- `T###` = Sequential task ID
- `[P]` = Parallelizable (can be done concurrently with other [P] tasks)
- `[US#]` = User Story label (maps to spec.md user stories)

---

## Phase 1: Setup

**Goal**: Prepare development environment and verify prerequisites

**Tasks**:

- [x] T001 Verify AI Assistant service is running on port 9011
- [x] T002 Verify main Flask application runs on port 5010
- [x] T003 Create feature branch from latest master: `git checkout master && git pull && git checkout -b 001-grading-core-creation`
- [x] T004 Backup files that will be modified for easy rollback reference

**Completion Criteria**:
- AI service responds to `http://127.0.0.1:9011/health`
- Flask app responds to `http://127.0.0.1:5010`
- All backup files created in `.backup/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Implement shared infrastructure that all user stories depend on

**Tasks**:

- [x] T005 [P] Add AI prompt templates to `config.py` - Add `NAME_GENERATION_PROMPT` and `COURSE_EXTRACTION_PROMPT` following existing prompt structure pattern
- [x] T006 [P] Create metadata extraction service in `services/ai_service.py` - Add `generate_core_name()` and `extract_course_name()` functions
- [x] T007 Update `grading_core/factory.py` - Add fallback "未分类" for missing COURSE attribute in `get_all_strategies()` method

**Completion Criteria**:
- Prompt templates follow existing `BASE_CREATOR_PROMPT` structure
- Service functions include error handling and logging per NFR-001
- Factory returns "未分类" instead of None for missing COURSE

---

## Phase 3: User Story 1 - Reorganized Core Creation UI (P1)

**Priority**: P1 (Critical)
**Independent Test**: Navigate to `/ai_generator` and verify field order is correct for both forms

**Goal**: Reorder form fields to follow logical workflow: documents → parameters → instructions → naming

### Backend API Routes

- [x] T008 [US1] Add `POST /api/ai/generate_name` route in `blueprints/ai_generator.py` - Call service function, return JSON response with status, name, confidence
- [x] T009 [US1] Add `POST /api/ai/extract_course` route in `blueprints/ai_generator.py` - Call service function, return JSON response with status, course_name, source

### Frontend Templates

- [x] T010 [P] [US1] Reorganize `templates/components/form_logic.html` - Reorder fields: (1) exam upload, (2) standard upload, (3) max score, (4) strictness, (5) extra prompt, (6) core name with auto-generate button, (7) course name with auto-fill
- [x] T011 [P] [US1] Reorganize `templates/components/form_direct.html` - Reorder fields to match Logic Core form order
- [x] T012 [US1] Add auto-generate button UI in both forms - Add "✨ AI生成" button next to core name input with loading state and error handling
- [x] T013 [US1] Add auto-fill JavaScript for course name - Trigger on both files selected, call `/api/ai/extract_course`, populate course_name field
- [x] T014 [US1] Add auto-generate JavaScript for core name - Trigger on button click, call `/api/ai/generate_name`, populate task_name field
- [x] T015 [US1] Add loading states and error handling for AI calls - Show spinner during API calls, display error message on failure (manual entry still allowed)

**Completion Criteria**:
- Fields appear in correct order in both Logic Core and Direct AI Core forms
- Course name auto-fills when both documents selected
- Core name generates on button click
- All visual styling preserved (glass-panel, hover states, transitions)
- Existing functionality intact (file modal, regeneration, strictness, max score)

---

## Phase 4: User Story 3 - Fixed Core Selection in Task Creation (P1)

**Priority**: P1 (Critical)
**Independent Test**: Navigate to `/new_class` and verify dropdown shows actual core names

**Goal**: Fix core selection dropdown to display actual core names and course names

### Backend Fixes

- [x] T016 [US3] Verify `grading_core/factory.py` fallback is working - Ensure `get_all_strategies()` returns "未分类" for missing COURSE
- [x] T017 [US3] Update `blueprints/grading.py` new_class route - Pass strategies with proper course names to template

### Frontend Template

- [x] T018 [P] [US3] Fix `templates/newClass.html` core dropdown - Replace `{{ course }}` with `{{ course or '未分类' }}` to handle None values
- [x] T019 [US3] Update dropdown JavaScript `selectStrategy()` function - Ensure course name auto-fills correctly when core is selected
- [x] T020 [US3] Update dropdown search/filter logic - Ensure filter works with both core names and course names

**Completion Criteria**:
- No "None" or "Generic Course" displayed in dropdown
- All cores show actual core names
- Cores with missing course show "未分类"
- Selecting a core auto-fills course name field
- Search/filter works correctly

---

## Phase 5: User Story 2 - AI Auto-Generation of Core Names (P2)

**Priority**: P2 (Enhancement)
**Independent Test**: Upload documents and click auto-generate, verify meaningful names

**Goal**: Implement AI-powered core name generation with proper format

### Service Layer Enhancement

- [x] T021 [P] [US2] Enhance `generate_core_name()` in `services/ai_service.py` - Add document content analysis for better name suggestions when filenames are unclear

### Frontend Enhancement

- [x] T022 [US2] Add confidence display to auto-generation - Show confidence score from AI response, allow user to accept or regenerate
- [x] T023 [US2] Add regenerate option - Allow user to click "重新生成" if not satisfied with suggested name
- [x] T024 [US2] Add name format validation - Ensure generated name follows `[Year/Season]-[CourseName]-[AssignmentType]批改核心` format

**Completion Criteria**:
- 90% of names generated successfully with good metadata
- Generated names follow specified format
- User can regenerate if not satisfied
- Manual override always available

---

## Phase 6: User Story 4 - Unified Naming Convention (P2)

**Priority**: P2 (Enhancement)
**Independent Test**: Create both core types and verify consistent display

**Goal**: Ensure consistent naming across Logic Cores and Direct AI Cores

### AI Generation Prompt Update

- [x] T025 [US4] Update `BASE_CREATOR_PROMPT` in `config.py` - Add instruction for AI to set COURSE class attribute in generated graders
- [x] T026 [US4] Update Direct AI core generation prompt - Ensure COURSE attribute is set for Direct AI cores as well

### Verification

- [x] T027 [US4] Add validation in core creation routes - Ensure `name` and `course_name` are non-NULL before saving to database

**Completion Criteria**:
- All new cores have non-NULL name and course_name
- Both core types display consistently in dropdown
- COURSE attribute is set in generated grader classes

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Final validation, testing, and documentation

**Tasks**:

- [ ] T028 Perform regression testing - Verify all existing functionality works: file upload, regeneration, strictness, extra prompts, student list selection, grade export
- [ ] T029 Test AI service failure scenarios - Stop ai_assistant.py, verify manual entry still works, error messages are clear
- [ ] T030 Test legacy cores with NULL course names - Verify "未分类" fallback displays correctly
- [ ] T031 Measure page load times - Verify core creation and task creation pages load under 2 seconds
- [ ] T032 Measure auto-fill response time - Verify course name extraction completes under 3 seconds
- [ ] T033 Verify visual consistency - Check all affected pages for preserved styling: glass-panel effects, hover states, transitions, colors
- [ ] T034 Update quickstart.md testing checklist - Mark all tested items as complete
- [ ] T035 Create pull request to master branch - Include summary of changes, testing results, and screenshots of UI

**Completion Criteria**:
- All regression tests pass
- AI failure scenarios handled gracefully
- Performance metrics met (load <2s, auto-fill <3s)
- No visual regressions
- Documentation updated
- PR ready for review

---

## Dependencies

### Story Completion Order

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
┌─────────────┬─────────────┐
│   Phase 3   │   Phase 4   │  ← Can execute in parallel
│   [US1-P1]  │   [US3-P1]  │
└─────────────┴─────────────┘
    ↓               ↓
┌─────────────┬─────────────┐
│   Phase 5   │   Phase 6   │  ← Can execute in parallel
│   [US2-P2]  │   [US4-P2]  │
└─────────────┴─────────────┘
    ↓
Phase 7 (Polish)
```

### Critical Path

1. **T007 (Factory fallback)** must complete before **T016-T020 (US3)**
2. **T008-T009 (API routes)** must complete before **T013-T015 (Frontend JS)**
3. **T025 (Prompt update)** should complete before testing US4

### Parallel Execution Opportunities

| Task Group | Parallel Tasks | Notes |
|------------|----------------|-------|
| Phase 2 | T005, T006, T007 | Config, service, factory are independent |
| Phase 3 | T010, T011 | Both form templates can be edited in parallel |
| Phase 5 | T021 | Service layer independent of frontend |
| Phase 6 | T025, T026 | Both prompts can be updated in parallel |

---

## Implementation Strategy

### MVP (Minimum Viable Product)

**Scope**: Phase 1 + Phase 2 + Phase 3 + Phase 4

**Delivers**:
- Reorganized core creation UI (both forms)
- Fixed core selection dropdown in task creation
- Factory fallback for missing course names

**Value**: Addresses both P1 (critical) user stories

### Incremental Delivery

**Sprint 1**: Complete MVP (Phases 1-4)
**Sprint 2**: Add AI auto-generation enhancements (Phase 5)
**Sprint 3**: Ensure naming consistency (Phase 6)
**Sprint 4**: Polish and validation (Phase 7)

---

## Testing Checklist Per User Story

### US1: Reorganized Core Creation UI

- [ ] Logic Core form fields in correct order
- [ ] Direct AI Core form fields in correct order
- [ ] Course name auto-fills when both files selected
- [ ] Core name auto-generates on button click
- [ ] Visual styling preserved
- [ ] File modal selection still works
- [ ] Regeneration from existing tasks works

### US2: AI Auto-Generation of Core Names

- [ ] Well-named documents produce good names
- [ ] Poorly named documents extract content for names
- [ ] AI service unavailable shows error, allows manual entry
- [ ] Generated names follow format
- [ ] User can edit generated names

### US3: Fixed Core Selection in Task Creation

- [ ] No "None" in dropdown
- [ ] All cores show actual names
- [ ] Legacy cores show "未分类"
- [ ] Selecting core auto-fills course name
- [ ] Search/filter works correctly

### US4: Unified Naming Convention

- [ ] Both core types display consistently
- [ ] New cores have non-NULL name and course_name
- [ ] Dropdown sorting is consistent

---

## Format Validation

All tasks follow the checklist format:
- ✅ Checkbox `- [ ]`
- ✅ Task ID `T###`
- ✅ `[P]` marker for parallelizable tasks
- ✅ `[US#]` label for user story tasks (Phases 3-6)
- ✅ Clear description with file path

---

## Risk Mitigation

| Risk | Mitigation Task |
|------|-----------------|
| Visual regression | T033 - Visual consistency verification |
| AI service unavailable | T015, T029 - Error handling testing |
| Performance degradation | T031, T032 - Performance measurement |
| Breaking existing features | T028 - Regression testing |
| Incomplete field reordering | Visual QA of both forms |

---

## Next Steps

1. Start with Phase 1 (Setup) tasks
2. Proceed to Phase 2 (Foundational)
3. Execute Phase 3 and Phase 4 in parallel for MVP delivery
4. Complete remaining phases incrementally

**Command to start implementation**: `/speckit.implement`
