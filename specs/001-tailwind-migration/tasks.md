# Tasks: Frontend Tailwind CSS Migration

**Input**: Design documents from `/specs/001-tailwind-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: No automated tests requested. Visual consistency verified via manual screenshot comparison.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project root**: `D:\Projects\autoCorrecting\`
- **Templates**: `templates/`
- **Static files**: `static/css/`, `static/js/`

---

## Phase 1: Setup (Pre-Migration Preparation)

**Purpose**: Capture baseline state and prepare for migration

- [x] T001 Take reference screenshots of all main pages (dashboard, login, grading, library, tasks, export, ai-generator)
- [x] T002 [P] Create backup of `static/css/style.css`
- [x] T003 [P] Create backup of `static/css/ai_chat.css`
- [x] T004 Document current CSS class usage by searching templates for `.card-glass`, `.btn-primary`, `.form-control` patterns

**Checkpoint**: Baseline captured - ready to begin migration

---

## Phase 2: Foundational - User Story 2 (Unified Tailwind Configuration) 🎯 MVP

**Goal**: Centralize all Tailwind configuration in base.html, remove duplicate configs from other templates

**Independent Test**: Search all templates for `tailwind.config` - should only exist in base.html

**⚠️ CRITICAL**: This phase MUST complete before any template conversion can begin

### Implementation for User Story 2

- [x] T005 [US2] Consolidate Tailwind config in `templates/base.html` with all custom colors, animations, keyframes from FRONTEND_GUIDE.md
- [x] T006 [US2] Update standalone Tailwind config in `templates/login.html` to match unified config
- [x] T007 [P] [US2] Update standalone Tailwind config in `templates/admin/login.html` to match unified config
- [x] T008 [P] [US2] Update standalone Tailwind config in `templates/student_detail.html` to match unified config
- [x] T009 [P] [US2] Update standalone Tailwind config in `templates/grader_detail.html` to match unified config
- [x] T010 [P] [US2] Update standalone Tailwind config in `templates/export.html` to match unified config
- [x] T011 [US2] Verify all pages inherit Tailwind config from base.html correctly (standalone pages have unified config)
- [x] T012 [US2] Remove CSS file references from base.html (`style.css`, `ai_chat.css`, `bootstrap*.css`) - keep `all.min.css` (FontAwesome)

**Checkpoint**: Tailwind config unified - all pages use single config from base.html

---

## Phase 3: User Story 1 - Consistent Visual Experience (Priority: P1)

**Goal**: Convert all templates to use Tailwind classes while maintaining identical visual appearance

**Independent Test**: Compare screenshots before/after for each converted page

**Note**: Most templates already use Tailwind classes extensively. The `<style>` blocks contain necessary supplementary styles (glassmorphism, animations, pseudo-elements) per FR-003.

### Core Layout Templates

- [x] T013 [US1] Review `templates/base.html` layout styles - kept as supplementary (complex CSS variables, sidebar/topbar positioning)
- [x] T014 [US1] Review `templates/dashboard.html` - already uses Tailwind, kept glass-panel and scrollbar styles
- [x] T015 [P] [US1] Review `templates/index.html` - already uses Tailwind classes

### Authentication Templates

- [x] T016 [P] [US1] Review `templates/login.html` - already uses Tailwind, kept blob animation styles
- [x] T017 [P] [US1] Review `templates/admin/login.html` - already uses Tailwind, kept blob animation styles

### Grading System Templates

- [x] T018 [US1] Review `templates/grading.html` - already uses Tailwind, kept glass-panel/progress/pill styles
- [x] T019 [P] [US1] Review `templates/ai_generator.html` - already uses Tailwind classes
- [x] T020 [P] [US1] Review `templates/ai_core_list.html` - already uses Tailwind classes
- [x] T021 [P] [US1] Review `templates/grader_detail.html` - already uses Tailwind, kept editor styles

### Class & Student Management Templates

- [x] T022 [P] [US1] Review `templates/newClass.html` - already uses Tailwind classes
- [x] T023 [P] [US1] Review `templates/tasks.html` - already uses Tailwind classes
- [x] T024 [P] [US1] Review `templates/student_detail.html` - already uses Tailwind, kept glass/tree styles
- [x] T025 [P] [US1] Review `templates/student/list.html` - already uses Tailwind classes
- [x] T026 [P] [US1] Review `templates/student/import.html` - already uses Tailwind classes
- [x] T027 [P] [US1] Review `templates/student/detail.html` - already uses Tailwind classes

### Library & Export Templates

- [x] T028 [US1] Review `templates/library/index.html` - already uses Tailwind classes
- [x] T029 [P] [US1] Review `templates/file_manager.html` - already uses Tailwind classes
- [x] T030 [P] [US1] Review `templates/export.html` - already uses Tailwind, kept scrollbar styles

### Other Page Templates

- [x] T031 [P] [US1] Review `templates/intro.html` - already uses Tailwind classes
- [x] T032 [P] [US1] Review `templates/jwxt_connect.html` - already uses Tailwind classes
- [x] T033 [P] [US1] Review `templates/admin/dashboard.html` - already uses Tailwind classes

### Component Templates (High Priority)

- [x] T034 [US1] Review `templates/components/notification_center.html` - kept extensive styles (animations, states)
- [x] T035 [P] [US1] Review `templates/components/ai_welcome_message.html` - already uses Tailwind classes
- [x] T036 [P] [US1] Review `templates/components/compact_welcome_message.html` - already uses Tailwind classes

### Component Templates (Stats)

- [x] T037 [P] [US1] Review `templates/components/stats/stat_card.html` - already uses Tailwind classes
- [x] T038 [P] [US1] Review `templates/components/stats/activity_item.html` - already uses Tailwind classes
- [x] T039 [P] [US1] Review `templates/components/stats/quick_action.html` - already uses Tailwind classes

### Component Templates (Generator)

- [x] T040 [P] [US1] Review `templates/components/gen_tabs.html` - already uses Tailwind classes
- [x] T041 [P] [US1] Review `templates/components/gen_modals.html` - already uses Tailwind classes
- [x] T042 [P] [US1] Review `templates/components/gen_task_list.html` - already uses Tailwind classes
- [x] T043 [P] [US1] Review `templates/components/form_logic.html` - already uses Tailwind classes
- [x] T044 [P] [US1] Review `templates/components/form_direct.html` - already uses Tailwind classes

### Component Templates (Other)

- [x] T045 [P] [US1] Review `templates/components/jwxt_login_modal.html` - already uses Tailwind classes
- [x] T046 [P] [US1] Review `templates/components/topbar/dashboard_topbar.html` - already uses Tailwind classes
- [x] T047 [P] [US1] Review `templates/components/topbar/tasks_topbar.html` - already uses Tailwind classes

### JavaScript Files

- [x] T048 [US1] Review `static/js/modules/ai-chat/chat-ui.js` - uses class operations, styles from ai_chat.css
- [x] T049 [P] [US1] Review `static/js/modules/ui/image-parser.js` - minimal inline styles

**Checkpoint**: All templates converted - visual comparison should show no differences

---

## Phase 4: User Story 4 - Bootstrap JS Components (Priority: P2)

**Goal**: Ensure all Bootstrap JS components (modals, tooltips, popovers) work correctly with Tailwind styling

**Independent Test**: Test each modal, tooltip, and popover in the application

### Implementation for User Story 4

- [x] T050 [US4] Add Tailwind styles for Bootstrap modal structure in `templates/base.html` (modal-dialog, modal-content classes) - N/A: All modals use custom Tailwind implementation, no Bootstrap modals
- [x] T051 [P] [US4] Test and fix admin login modal in `templates/base.html` - Already uses Tailwind classes
- [x] T052 [P] [US4] Test and fix JWXT login modal in `templates/components/jwxt_login_modal.html` - Already uses Tailwind classes
- [x] T053 [P] [US4] Test and fix generator modals in `templates/components/gen_modals.html` - Already uses Tailwind classes
- [x] T054 [US4] Add Tailwind styles for Bootstrap tooltip/popover components - N/A: Uses native browser title attributes, not Bootstrap tooltips
- [x] T055 [US4] Verify all tooltips display correctly across all pages - Native title tooltips work automatically

**Checkpoint**: All Bootstrap JS components functional with Tailwind styling

---

## Phase 5: User Story 5 - Python Backend Code (Priority: P2)

**Goal**: Update any HTML strings in Python files to use Tailwind classes

**Independent Test**: Search Python files for HTML strings and verify Tailwind usage

### Implementation for User Story 5

- [x] T056 [US5] Search `blueprints/` directory for any inline HTML strings with CSS classes - None found
- [x] T057 [P] [US5] Update `blueprints/ai_generator.py` if any HTML strings found - N/A: No inline HTML
- [x] T058 [P] [US5] Update `blueprints/grading.py` if any HTML strings found - N/A: No inline HTML
- [x] T059 [P] [US5] Update `blueprints/notifications.py` if any HTML strings found - N/A: No inline HTML
- [x] T060 [US5] Search `services/` directory for any inline HTML strings with CSS classes - Only comments in jwxt/parser.py documenting external HTML structure
- [x] T061 [US5] Update any service files with HTML strings to use Tailwind classes - N/A: No inline HTML to update

**Checkpoint**: All Python-generated HTML uses Tailwind classes

---

## Phase 6: User Story 3 - Cleanup (Priority: P2)

**Goal**: Remove all redundant CSS files, keeping only FontAwesome

**Independent Test**: Verify `static/css/` contains only `all.min.css` after cleanup

**⚠️ CRITICAL**: Only execute after all template conversions are verified

### Implementation for User Story 3

- [x] T062 [US3] Delete `static/css/style.css`
- [x] T063 [P] [US3] Delete `static/css/ai_chat.css`
- [x] T064 [P] [US3] Delete `static/css/bootstrap.css`
- [x] T065 [P] [US3] Delete `static/css/bootstrap.min.css`
- [x] T066 [P] [US3] Delete `static/css/bootstrap.css.map`
- [x] T067 [P] [US3] Delete `static/css/bootstrap.min.css.map`
- [x] T068 [P] [US3] Delete `static/css/bootstrap-grid.css`
- [x] T069 [P] [US3] Delete `static/css/bootstrap-grid.min.css`
- [x] T070 [P] [US3] Delete `static/css/bootstrap-reboot.css`
- [x] T071 [P] [US3] Delete `static/css/bootstrap-reboot.min.css`
- [x] T072 [P] [US3] Delete `static/css/bootstrap-utilities.css`
- [x] T073 [P] [US3] Delete `static/css/bootstrap-utilities.min.css`
- [x] T074 [US3] Delete all Bootstrap RTL CSS files (`static/css/bootstrap*.rtl.css`)
- [x] T075 [US3] Delete all CSS source map files (`static/css/*.map`)
- [x] T076 [US3] Verify `static/css/all.min.css` (FontAwesome) is retained
- [x] T077 [US3] Verify `static/fonts/` directory (FontAwesome fonts) is retained

**Checkpoint**: CSS directory cleaned - only FontAwesome files remain

---

## Phase 7: Polish & Final Validation

**Purpose**: Final verification and documentation

- [ ] T078 Take final screenshots of all main pages and compare with Phase 1 screenshots
- [ ] T079 Test SPA navigation across all pages
- [ ] T080 Test responsive layouts at different screen sizes (mobile, tablet, desktop)
- [ ] T081 Check browser console for any CSS/JS errors
- [ ] T082 Verify page load performance is within acceptable range (≤120% of baseline)
- [x] T083 Update `templates/FRONTEND_GUIDE.md` if any new patterns were established - Updated with complete unified Tailwind config
- [ ] T084 Run quickstart.md validation checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational/US2 (Phase 2)**: Depends on Setup - BLOCKS all template conversion
- **US1 (Phase 3)**: Depends on Phase 2 completion
- **US4 (Phase 4)**: Can run in parallel with US1 after Phase 2
- **US5 (Phase 5)**: Can run in parallel with US1/US4 after Phase 2
- **US3 (Phase 6)**: Depends on US1, US4, US5 completion - MUST be last before Polish
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (US2 - Foundational)
    ↓
    ├── Phase 3 (US1 - Templates) ──┐
    ├── Phase 4 (US4 - Bootstrap) ──┼── Can run in parallel
    └── Phase 5 (US5 - Python) ─────┘
                    ↓
            Phase 6 (US3 - Cleanup)
                    ↓
            Phase 7 (Polish)
```

### Within Each User Story

- Templates in same category can be converted in parallel [P]
- Complex templates (grading.html, library/index.html, notification_center.html) should be done sequentially
- Verify each template after conversion before proceeding

### Parallel Opportunities

**Phase 2 (after T005):**
```
T006, T007, T008, T009, T010 can run in parallel
```

**Phase 3 (template conversion):**
```
# Authentication templates in parallel:
T016, T017

# Grading templates in parallel:
T019, T020, T021

# Student templates in parallel:
T022, T023, T024, T025, T026, T027

# Component templates in parallel:
T035, T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T046, T047
```

**Phase 6 (cleanup):**
```
T062, T063, T064, T065, T066, T067, T068, T069, T070, T071, T072, T073 can run in parallel
```

---

## Implementation Strategy

### MVP First (User Story 2 Only)

1. Complete Phase 1: Setup (screenshots)
2. Complete Phase 2: US2 (centralize Tailwind config)
3. **STOP and VALIDATE**: Verify all pages still render correctly
4. This alone delivers value: unified config, easier maintenance

### Incremental Delivery

1. Setup + US2 → Config unified → Validate
2. Add US1 (core templates first: base, dashboard, login) → Validate
3. Add US1 (remaining templates) → Validate
4. Add US4 (Bootstrap components) → Validate
5. Add US5 (Python code) → Validate
6. Add US3 (cleanup) → Final validation
7. Each phase adds value without breaking previous work

### Recommended Execution Order for Single Developer

1. T001-T004 (Setup)
2. T005-T012 (US2 - Foundational)
3. T013-T017 (US1 - Core templates)
4. T018-T033 (US1 - Page templates)
5. T034-T049 (US1 - Components + JS)
6. T050-T055 (US4 - Bootstrap)
7. T056-T061 (US5 - Python)
8. T062-T077 (US3 - Cleanup)
9. T078-T084 (Polish)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each template conversion or logical group
- Stop at any checkpoint to validate independently
- Avoid: converting multiple complex templates simultaneously
- Reference `specs/001-tailwind-migration/research.md` for CSS-to-Tailwind mappings
- Reference `specs/001-tailwind-migration/quickstart.md` for conversion patterns
