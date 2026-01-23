# Tasks: 全局 AI 助手重构 (Completion Phase)

**Input**: Design documents from `/specs/002-global-ai-assistant/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/ ✅

**Current Status**: ~95% Complete
**Scope**: This task list covers the remaining work to complete and stabilize the feature

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Implementation Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Database Schema | ✅ Done | `database.py:323-364` |
| API Blueprint | ✅ Done | `blueprints/ai_assistant.py` |
| Service Layer | ✅ Done | `services/ai_conversation_service.py` |
| Content Generation | ✅ Done | `services/ai_content_service.py:511-749` |
| Prompts | ✅ Done | `services/ai_prompts.py:234-412` |
| Frontend Widget | ✅ Done | `templates/components/ai_assistant_widget.html` |
| Core JavaScript | ✅ Done | `static/js/ai-assistant.js` |
| Blueprint Registration | ✅ Done | `app.py:7,72` |
| AI Endpoint Config | ✅ Done | `config.py:11-12` |
| Legacy Code Cleanup | 🔄 Pending | Old AI button in base.html |
| Operation Triggers | 🔄 Pending | Integration points not added |
| Error Handling | 🔄 Pending | Toast notifications |

---

## Phase 1: Cleanup & Verification (No Functional Risk)

**Purpose**: Remove legacy code and verify existing implementation works

**⚠️ SAFETY**: These tasks only remove/verify code, they do NOT add new functionality

- [ ] T001 Verify AI microservice starts: run `python ai_assistant.py` on port 9011
- [ ] T002 Verify Flask app starts without errors: run `python app.py` on port 5010
- [X] T003 Remove legacy AI chat button `#ai-chat-fab` in `templates/base.html:806-810`
- [X] T004 Remove legacy AI chat modal `#ai-chat-modal` in `templates/base.html:812-835`

**Checkpoint**: No duplicate AI buttons on page, services start cleanly

---

## Phase 2: End-to-End Validation (Testing Only)

**Purpose**: Validate complete message flow WITHOUT any code changes

**⚠️ SAFETY**: This phase only tests. If tests fail, bugs are documented for Phase 3.

### User Story 1 Tests - 浮窗入口

- [ ] T005 [US1] Test: Login and verify floating button visible in bottom-right corner
- [ ] T006 [US1] Test: Click button, verify panel expands with animation
- [ ] T007 [US1] Test: Send message "你好", verify loading animation shows
- [ ] T008 [US1] Test: Verify AI response received with typewriter effect
- [ ] T009 [US1] Test: Close panel, verify it collapses with animation
- [ ] T010 [US1] Test: Reopen panel, verify message history preserved

### User Story 2 Tests - 页面切换问候

- [ ] T011 [US2] Test: Navigate from dashboard to AI generator page
- [ ] T012 [US2] Test: Verify AI greeting appears (if rate limit allows)
- [ ] T013 [US2] Test: Navigate again within 60s, verify no new greeting

### User Story 5 Tests - 历史持久化

- [ ] T014 [US5] Test: Click "新建对话", verify panel clears
- [ ] T015 [US5] Test: Send message in new conversation
- [ ] T016 [US5] Test: Refresh page, verify history loads

**Checkpoint**: Document any failures → create bug fix tasks for Phase 3

---

## Phase 3: Bug Fixes (As Needed)

**Purpose**: Fix issues discovered during Phase 2 testing

**Note**: Only populate this phase based on Phase 2 test results

- [ ] T017 [BUG] Placeholder for bug fixes - add specific tasks based on test failures

---

## Phase 4: User Story 3 - Operation Feedback Triggers (P2)

**Goal**: Add AI feedback after key operations complete

**Independent Test**: Generate a grader, verify AI pops up with feedback

**⚠️ SAFETY**: Only ADD JavaScript calls at END of existing success callbacks. Does NOT modify core logic.

### Integration Tasks

- [ ] T018 [P] [US3] Add trigger call in `templates/ai_generator.html` after grader generation success
- [ ] T019 [P] [US3] Add trigger call in `templates/student/import.html` after student import success
- [ ] T020 [P] [US3] Add trigger call in `templates/new_class.html` after class creation success
- [ ] T021 [P] [US3] Add trigger call in export templates after export completion

**Integration Pattern**:
```javascript
// Add at END of success callback (after existing logic):
if (window.AIAssistant && window.AIAssistant.triggerOperationFeedback) {
    window.AIAssistant.triggerOperationFeedback('generate_grader', 'success', {
        grader_name: data.grader_name || '批改核心'
    });
}
```

**Checkpoint**: All four operation triggers integrated and working

---

## Phase 5: Error Handling Enhancement (Low Risk)

**Goal**: Show user-friendly error messages on failures

**⚠️ SAFETY**: Only adds code in catch/error blocks, does NOT change happy path

- [ ] T022 [US4] Add Toast notification in `static/js/ai-assistant.js` sendMessage catch block
- [ ] T023 [US4] Add Toast notification for connection timeout
- [ ] T024 [US4] Test: Stop AI microservice temporarily, verify error toast appears

**Error Handling Pattern**:
```javascript
catch (error) {
    hideLoading();
    if (window.showToast) {
        window.showToast('消息发送失败，请稍后重试', 'error');
    }
    console.error('[AIAssistant] Error:', error);
}
```

**Checkpoint**: Graceful error handling verified

---

## Phase 6: Polish (Optional Enhancements)

**Purpose**: Nice-to-have improvements, NOT required for release

**⚠️ OPTIONAL**: These can be skipped entirely if time is limited

- [ ] T025 [P] [OPT] Extract CSS from `templates/components/ai_assistant_widget.html` to `static/css/ai-assistant.css`
- [ ] T026 [P] [OPT] Add `Ctrl+/` keyboard shortcut to toggle widget
- [ ] T027 [P] [OPT] Add `Esc` key to close widget
- [ ] T028 [OPT] Add Markdown rendering using existing `marked.min.js`
- [ ] T029 [OPT] Add conversation history list panel

---

## Dependencies & Execution Order

```
Phase 1 (Cleanup)       → No dependencies, START HERE
       ↓
Phase 2 (Validation)    → Requires Phase 1 complete
       ↓
Phase 3 (Bug Fixes)     → Based on Phase 2 results
       ↓
┌──────┴──────┐
↓             ↓
Phase 4     Phase 5     → Can run in PARALLEL
(Triggers)  (Errors)
       ↓
Phase 6 (Polish)        → OPTIONAL, can skip
```

### Parallel Opportunities Within Phases

**Phase 1**: T003, T004 can run in parallel (different line ranges)
**Phase 4**: T018, T019, T020, T021 ALL parallel (different files)
**Phase 5**: T022, T023 sequential (same file), T024 after both
**Phase 6**: T025, T026, T027 ALL parallel (different files/features)

---

## Risk Assessment

| Phase | Risk Level | Reason |
|-------|------------|--------|
| Phase 1 | 🟢 Low | Only removal/verification |
| Phase 2 | 🟢 None | Testing only, no code changes |
| Phase 3 | 🟡 Medium | Bug fixes (depends on findings) |
| Phase 4 | 🟢 Low | Adding calls at end of callbacks |
| Phase 5 | 🟢 Low | Adding error handling in catch blocks |
| Phase 6 | 🟢 Low | Optional, can be reverted easily |

---

## MVP Completion Checklist

**Already Complete** (from previous implementation):
- [x] Floating widget visible on all pages
- [x] Chat panel expands/collapses with animation
- [x] Send message and receive AI response
- [x] Typewriter effect for AI messages
- [x] Message history persists across refresh
- [x] Page switch triggers greeting (with rate limit)
- [x] New conversation button works
- [x] Blueprint registered in app.py
- [x] AI endpoint configured in config.py

**Remaining for Release** (this task list):
- [ ] Legacy AI button removed (T003-T004)
- [ ] End-to-end flow validated (T005-T016)
- [ ] Any discovered bugs fixed (T017)
- [ ] Operation feedback triggers (T018-T021) - RECOMMENDED
- [ ] Error toast notifications (T022-T024) - RECOMMENDED

**Optional Polish**:
- [ ] CSS extraction, keyboard shortcuts, Markdown

---

## Summary

| Metric | Value |
|--------|-------|
| Total Remaining Tasks | 29 |
| Cleanup Tasks | 4 |
| Validation Tasks | 12 |
| Bug Fix Placeholder | 1 |
| Operation Trigger Tasks | 4 |
| Error Handling Tasks | 3 |
| Optional Polish Tasks | 5 |
| Parallel Opportunities | 11 tasks marked [P] |
| Estimated Effort | ~2-4 hours |

---

## Notes

- Feature is ~95% complete; focus on validation and integration
- All new code uses existing `window.AIAssistant` public API
- No changes needed to Flask routes, database, or service logic
- Rollback: Revert template changes if issues arise
- Skip Phase 6 entirely if time-constrained
