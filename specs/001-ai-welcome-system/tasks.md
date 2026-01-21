# Tasks: AI Welcome Message System

**Input**: Design documents from `/specs/001-ai-welcome-system/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml

**Tests**: Tests are not explicitly requested in the feature specification, so test tasks are OPTIONAL and marked as such.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database initialization and configuration for the AI welcome system

- [X] T001 Add AI_WELCOME_CACHE_TTL configuration constant (4 hours) in config.py
- [X] T002 Create ai_welcome_messages table with indexes in database.py
- [X] T003 Create tests/ai_welcome/ directory structure for test suite

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core AI content generation infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create PageContext enum in services/ai_prompts.py
- [X] T005 [P] Define WELCOME_PROMPT_TEMPLATE with few-shot examples in services/ai_prompts.py
- [X] T006 [P] Define time-based fallback messages in services/ai_prompts.py
- [X] T007 [P] Create WelcomeMessage dataclass in services/ai_content_service.py
- [X] T008 [P] Create MessageContext dataclass in services/ai_content_service.py
- [X] T009 [P] Implement validate_message_content() function in services/ai_content_service.py
- [X] T010 Implement generate_welcome_message() async function in services/ai_content_service.py
- [X] T011 Implement get_cached_message() function in services/ai_content_service.py
- [X] T012 Implement save_to_cache() function in services/ai_content_service.py
- [X] T013 Implement get_fallback_message() function in services/ai_content_service.py
- [X] T014 Create ai_welcome blueprint in blueprints/ai_welcome.py
- [X] T015 Implement GET /api/welcome/messages endpoint in blueprints/ai_welcome.py
- [X] T016 Implement POST /api/welcome/messages/refresh endpoint in blueprints/ai_welcome.py
- [X] T017 Implement GET /api/welcome/fallback endpoint in blueprints/ai_welcome.py
- [X] T018 Register ai_welcome blueprint in app.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dashboard Personalized Welcome (Priority: P1) 🎯 MVP

**Goal**: Display a personalized, contextually-aware AI-generated welcome message on the dashboard that provides emotional encouragement and suggests next actions.

**Independent Test**: Login to the system, navigate to the dashboard, and observe:
1. A welcome message appears (streaming animation from US4)
2. Message content is personalized (references time, user stats)
3. Message is appropriate for current time of day

### Implementation for User Story 1

- [X] T019 [P] [US1] Create ai_welcome_message.html component template in templates/components/
- [X] T020 [P] [US1] Create ai-welcome.js script in static/js/
- [X] T021 [US1] Implement loadWelcomeMessage() async function in static/js/ai-welcome.js
- [X] T022 [US1] Implement showFallbackMessage() function in static/js/ai-welcome.js
- [X] T023 [US1] Implement container height auto-resize logic in static/js/ai-welcome.js
- [X] T024 [US1] Integrate AI welcome component into dashboard.html (replace static message)
- [X] T025 [US1] Add user stats gathering logic in blueprints/main.py for dashboard context
- [X] T026 [US1] Pass page_context variable to template in blueprints/main.py

**Checkpoint**: At this point, User Story 1 should be fully functional - dashboard shows AI welcome message (without animation from US4)

---

## Phase 4: User Story 2 - Cross-Page Contextual Guidance (Priority: P2)

**Goal**: Display contextual hints or guidance relevant to each functional page (tasks, student list, AI generator, export).

**Independent Test**: Navigate to each functional page and verify:
1. A guidance message appears in the topbar
2. Message content is relevant to that page's functionality
3. Messages differ across pages

### Implementation for User Story 2

- [X] T027 [P] [US2] Create compact_welcome_message.html component for topbar in templates/components/
- [X] T028 [US2] Add topbar welcome slot to base.html (exclude login/admin pages)
- [X] T029 [US2] Implement page_context detection logic in static/js/ai-welcome.js
- [X] T030 [US2] Update loadWelcomeMessage() to handle compact display mode in static/js/ai-welcome.js
- [X] T031 [US2] Add page-specific prompt templates in services/ai_prompts.py (tasks, student_list, ai_generator, export)
- [X] T032 [US2] Integrate PageContext.from_path() in blueprints/ai_welcome.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - dashboard has full message, other pages show compact guidance

---

## Phase 5: User Story 3 - Cache Refresh on User Actions (Priority: P2)

**Goal**: Refresh welcome/guidance messages after write operations to reflect new context.

**Independent Test**: Perform write operations (create class, import students, generate grader) and verify:
1. Welcome message updates after each operation
2. New message suggests appropriate next steps

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement invalidate_cache() function in services/ai_content_service.py
- [X] T034 [P] [US3] Add cache refresh trigger in blueprints/ai_generator.py after grader generation
- [X] T035 [P] [US3] Add cache refresh trigger in blueprints/grading.py after class creation
- [X] T036 [P] [US3] Add cache refresh trigger in blueprints/student.py after student import
- [X] T037 [P] [US3] Add cache refresh trigger in blueprints/grading.py after submission
- [X] T038 [US3] Create refreshWelcomeMessage() client-side function in static/js/ai-welcome.js
- [X] T039 [US3] Call refreshWelcomeMessage() after write operations complete in static/js/ai-welcome.js

**Checkpoint**: All user stories should now be independently functional with cache refresh working

---

## Phase 6: User Story 4 - Streaming Display Effect (Priority: P3)

**Goal**: Display AI-generated content with a typewriter streaming effect on first view, instant display on subsequent views.

**Independent Test**: Clear localStorage, refresh page and verify:
1. First view shows character-by-character streaming animation
2. Refresh shows instant display
3. localStorage failure gracefully degrades to always streaming

### Implementation for User Story 4

- [X] T040 [P] [US4] Implement typewriter() function in static/js/ai-welcome.js
- [X] T041 [P] [US4] Add localStorage tracking for seen messages in static/js/ai-welcome.js
- [X] T042 [P] [US4] Create CSS @keyframes for cursor-blink animation in templates/components/ai_welcome_message.html
- [X] T043 [US4] Update loadWelcomeMessage() to detect first vs. repeat view in static/js/ai-welcome.js
- [X] T044 [US4] Add typewriter-cursor class styling in templates/components/ai_welcome_message.html
- [X] T045 [US4] Implement localStorage error handling (try-catch with fallback) in static/js/ai-welcome.js

**Checkpoint**: All user stories should now be complete with full streaming animation effect

---

## Phase 7: Optional Tests (OPTIONAL - Only if testing approach is confirmed)

> **NOTE: These tasks are OPTIONAL. Only include if TDD approach is confirmed.**

- [ ] T046 [P] [TEST] Unit test for validate_message_content() in tests/ai_welcome/test_service.py
- [ ] T047 [P] [TEST] Unit test for get_fallback_message() time periods in tests/ai_welcome/test_service.py
- [ ] T048 [P] [TEST] Unit test for WelcomeMessage.is_expired property in tests/ai_welcome/test_models.py
- [ ] T049 [P] [TEST] Unit test for MessageContext.from_request() in tests/ai_welcome/test_models.py
- [ ] T050 [TEST] Integration test for GET /api/welcome/messages endpoint in tests/ai_welcome/test_api.py
- [ ] T051 [TEST] Integration test for POST /api/welcome/messages/refresh endpoint in tests/ai_welcome/test_api.py
- [ ] T052 [TEST] Integration test for cache TTL expiration in tests/ai_welcome/test_service.py
- [ ] T053 [TEST] Mock AI service test for timeout/fallback behavior in tests/ai_welcome/test_service.py

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T054 [P] Add logging to ai_content_service.py for debugging AI generation
- [X] T055 [P] Add error handling for AI assistant service unavailability in services/ai_content_service.py
- [X] T056 [P] Add rate limit handling (HTTP 429) with stale cache serving in services/ai_content_service.py
- [X] T057 [P] Create cleanup_expired_messages() function in services/ai_content_service.py
- [X] T058 [P] Add comments to ai_welcome_messages table schema in database.py
- [ ] T059 Validate quickstart.md instructions work end-to-end (manual testing required)
- [ ] T060 Manually test all acceptance scenarios from spec.md (manual testing required)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← BLOCKS all user stories
    ↓
    ├→ Phase 3 (US1 - Dashboard) 🎯 MVP
    ├→ Phase 4 (US2 - Cross-Page)
    ├→ Phase 5 (US3 - Cache Refresh)
    └→ Phase 6 (US4 - Streaming Effect)
    ↓
Phase 7 (Optional Tests)
    ↓
Phase 8 (Polish)
```

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 component but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Builds on US1/US2 but independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Purely visual enhancement to US1/US2

**Key**: All user stories are fundamentally independent after Phase 2 completion.

### Within Each User Story

- Models and utilities can be done in parallel [P]
- Frontend component creation can be parallel [P]
- Integration tasks must follow component creation
- Service endpoints before frontend integration

### Parallel Opportunities

**Phase 2 (Foundational) - After T009:**
- T004, T005, T006 (ai_prompts.py)
- T007, T008, T009 (ai_content_service.py models)
- Then T010, T011, T012, T013 (service functions)
- Then T014-T018 (blueprint and registration)

**Phase 3 (US1) - After T026:**
- T019, T020 (component and script creation) [P]

**Phase 4 (US2) - After T032:**
- T027, T029 (component template and JS logic) [P]
- T031 (prompt templates) [P]

**Phase 5 (US3) - After T039:**
- T034, T035, T036, T037 (blueprint triggers) [P]

**Phase 6 (US4) - After T045:**
- T040, T041, T042, T044 (typewriter implementation) [P]

---

## Parallel Example: User Story 1

```bash
# Launch component and script creation together:
Task T019: "Create ai_welcome_message.html component template"
Task T020: "Create ai-welcome.js script"

# Wait for T019 and T020, then continue with T021-T026 sequentially
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T018) - **CRITICAL**
3. Complete Phase 3: User Story 1 (T019-T026)
4. **STOP and VALIDATE**: Test dashboard welcome independently
5. Deploy/demo if ready

**MVP Delivers**: Dashboard shows personalized AI welcome message with fallback support

### Incremental Delivery

1. **Setup + Foundational** → Foundation ready (T001-T018)
2. **+ User Story 1** → Dashboard welcome (T019-T026) → Deploy/Demo (MVP!)
3. **+ User Story 2** → Cross-page guidance (T027-T032) → Deploy/Demo
4. **+ User Story 3** → Cache refresh (T033-T039) → Deploy/Demo
5. **+ User Story 4** → Streaming effect (T040-T045) → Deploy/Demo

### Parallel Team Strategy

With multiple developers after Foundational phase:

- **Developer A**: User Story 1 (Dashboard) - T019-T026
- **Developer B**: User Story 2 (Cross-Page) - T027-T032
- **Developer C**: User Story 3 (Cache Refresh) - T033-T039
- **Developer D**: User Story 4 (Streaming) - T040-T045

Stories complete and integrate independently without conflicts.

---

## Summary

| Metric | Count | Completed |
|--------|-------|-----------|
| **Total Tasks** | 60 (53 required + 7 optional tests) | 51 / 60 |
| **Setup Phase** | 3 tasks | 3 / 3 ✅ |
| **Foundational Phase** | 15 tasks | 15 / 15 ✅ |
| **User Story 1 (P1)** | 8 tasks | 8 / 8 ✅ |
| **User Story 2 (P2)** | 6 tasks | 6 / 6 ✅ |
| **User Story 3 (P2)** | 7 tasks | 7 / 7 ✅ |
| **User Story 4 (P3)** | 6 tasks | 6 / 6 ✅ |
| **Optional Tests** | 8 tasks | 0 / 8 (optional) |
| **Polish Phase** | 7 tasks | 5 / 7 (2 manual tests remaining) |
| **Parallelizable Tasks** | 24 tasks marked [P] | 24 / 24 ✅ |

### Parallel Opportunities by Phase

| Phase | Sequential | Parallel | Total |
|-------|-----------|----------|-------|
| Setup | 0 | 3 | 3 |
| Foundational | 5 | 10 | 15 |
| US1 | 6 | 2 | 8 |
| US2 | 3 | 3 | 6 |
| US3 | 3 | 4 | 7 |
| US4 | 2 | 4 | 6 |
| Polish | 2 | 5 | 7 |

### Independent Test Criteria by Story

| Story | Test Criterion |
|-------|----------------|
| **US1** | Login → Dashboard → See personalized welcome message |
| **US2** | Navigate to tasks/student_list → See contextual guidance |
| **US3** | Create class → Dashboard message updates to suggest next step |
| **US4** | Clear localStorage → Refresh → See streaming animation |

### Suggested MVP Scope

**MVP = Phases 1 + 2 + 3** (Tasks T001-T026 = 26 tasks)

This delivers the core dashboard welcome message functionality without cross-page guidance, cache refresh triggers, or streaming animation. Those can be added in subsequent increments.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow FRONTEND_GUIDE.md for all UI components (glass panel, Tailwind, indigo color scheme)
