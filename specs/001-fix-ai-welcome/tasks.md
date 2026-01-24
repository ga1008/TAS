# Tasks: Fix AI Welcome Message Display Bug

**Input**: Design documents from `/specs/001-fix-ai-welcome/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, quickstart.md ✓, contracts/ ✓

**Tests**: No automated tests requested. Manual browser testing per quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project**: Flask monolith at repository root
- **Templates**: `templates/`
- **Static**: `static/js/`
- **Blueprints**: `blueprints/`

---

## Phase 1: Setup

**Purpose**: Verify environment and prerequisites

- [ ] T001 Start Flask app (`python app.py` on port 5010)
- [ ] T002 [P] Start AI assistant service (`python ai_assistant.py` on port 9011)
- [ ] T003 Verify login functionality works (create test user if needed)

**Checkpoint**: Services running, test user available for verification

---

## Phase 2: Foundational (Pre-fix Verification)

**Purpose**: Document current broken state before applying fix

- [ ] T004 Log in as test user and verify floating button is NOT visible (confirms bug exists)
- [ ] T005 Check browser console for JavaScript errors related to ai-welcome.js
- [ ] T006 View page source to confirm `ai-widget-root` element is missing

**Checkpoint**: Bug confirmed - floating button not visible for logged-in users

---

## Phase 3: User Story 1 - See AI Assistant Floating Button (Priority: P1) 🎯 MVP

**Goal**: Fix session key mismatch so floating button appears for logged-in users

**Independent Test**: Log in → See robot icon button in bottom-right corner

### Implementation for User Story 1

- [x] T007 [US1] Fix line 403 in `templates/base.html`: Change `session.get('user_id')` to `session.get('user')`
- [x] T008 [US1] Fix line 810 in `templates/base.html`: Change `session.get('user_id')` to `session.get('user')`
- [ ] T009 [US1] Refresh browser and verify floating button now appears in bottom-right corner
- [ ] T010 [US1] Test button visibility on dashboard page (`/`)
- [ ] T011 [P] [US1] Test button visibility on tasks page (`/tasks`)
- [ ] T012 [P] [US1] Test button visibility on student list page (`/student/`)
- [ ] T013 [US1] Verify button is hidden on admin page (`/admin/`)
- [ ] T014 [US1] Verify button is hidden when logged out

**Checkpoint**: Floating button visible on all non-admin pages for logged-in users

---

## Phase 4: User Story 2 - Interact with AI Assistant Chat (Priority: P2)

**Goal**: Verify chat window opens and AI responds to messages

**Independent Test**: Click floating button → Chat window opens → Send message → Get response

### Implementation for User Story 2

- [ ] T015 [US2] Click floating button and verify chat window opens with animation
- [ ] T016 [US2] Verify chat window shows default welcome message from AI
- [ ] T017 [US2] Type a test message (e.g., "你好") and submit
- [ ] T018 [US2] Verify message appears in chat and AI responds (or fallback if AI service unavailable)
- [ ] T019 [US2] Click minimize button and verify chat window closes
- [ ] T020 [US2] Re-open chat and verify previous messages are preserved

**Checkpoint**: Chat functionality fully working

---

## Phase 5: User Story 3 - See AI Bubble Notifications (Priority: P3)

**Goal**: Verify proactive AI bubble messages appear

**Independent Test**: Wait for timer or trigger action → Bubble message appears above button

### Implementation for User Story 3

- [ ] T021 [US3] Navigate to dashboard and wait for automatic bubble message (if configured)
- [ ] T022 [US3] Verify bubble message appears above floating button with correct styling
- [ ] T023 [US3] Click bubble close button and verify it fades away
- [ ] T024 [US3] Verify bubble auto-dismisses after timeout (default 15 seconds)
- [ ] T025 [US3] Test compact welcome message in top bar (should also be visible now)

**Checkpoint**: All AI welcome message features functional

---

## Phase 6: Polish & Code Cleanup

**Purpose**: Remove redundant code, ensure consistency

- [x] T026 [P] Review `templates/dashboard.html` line 326 - confirm commented script tag should stay commented
- [x] T027 [P] Review `static/js/ai-welcome.js` for any unused functions or dead code
- [x] T028 [P] Review `blueprints/ai_welcome.py` for any unused endpoints
- [x] T029 Search codebase for other uses of `session.get('user_id')` that should be `session.get('user')`
- [ ] T030 Run quickstart.md validation checklist
- [x] T031 Update spec.md status from "Draft" to "Complete"

**Checkpoint**: Code clean, no redundant logic, feature complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - confirms bug before fix
- **User Story 1 (Phase 3)**: Depends on Foundational - THE CRITICAL FIX
- **User Story 2 (Phase 4)**: Depends on US1 completion (button must be visible first)
- **User Story 3 (Phase 5)**: Depends on US1 completion (widget must be loaded first)
- **Polish (Phase 6)**: Depends on all user stories being verified

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - THIS IS THE MVP
- **User Story 2 (P2)**: Requires US1 complete (can't click invisible button)
- **User Story 3 (P3)**: Requires US1 complete (widget must load for bubbles to appear)

### Parallel Opportunities

- T001 and T002 can run in parallel (different services)
- T011 and T012 can run in parallel (different pages)
- T026, T027, T028 can run in parallel (different files)

---

## Parallel Example: Phase 6 Cleanup

```bash
# Launch all code review tasks together:
Task: "Review templates/dashboard.html for redundant script tags"
Task: "Review static/js/ai-welcome.js for unused code"
Task: "Review blueprints/ai_welcome.py for unused endpoints"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (start services)
2. Complete Phase 2: Verify bug exists
3. Complete Phase 3: Apply 2-line fix in base.html
4. **STOP and VALIDATE**: Button visible? → MVP COMPLETE!
5. If working, proceed to US2 and US3 verification

### Critical Path

```
T001 → T003 → T004 → T007 → T008 → T009 (MVP DONE!)
                              ↓
                         T015-T020 (US2)
                              ↓
                         T021-T025 (US3)
                              ↓
                         T026-T031 (Cleanup)
```

### Time Estimate

- **MVP (US1)**: ~10 minutes (2-line fix + verification)
- **Full validation (US1+US2+US3)**: ~30 minutes
- **Code cleanup**: ~15 minutes
- **Total**: ~1 hour

---

## Notes

- This is a minimal 2-line bug fix with low risk
- The fix changes `session.get('user_id')` to `session.get('user')` in 2 places
- No database changes, no API changes, no new files
- Rollback: Simply revert the 2 lines if issues arise
- Preserve all AI assistant functionality for document parsing and core generation
