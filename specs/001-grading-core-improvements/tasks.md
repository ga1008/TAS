# Tasks: Grading Core Improvements

**Input**: Design documents from `/specs/001-grading-core-improvements/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: Tests are NOT included in this task list as they were not explicitly requested in the feature specification. Manual testing scenarios are described in quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US2, US1, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `blueprints/`, `services/`, `grading_core/`, `templates/`, `database.py`
- **Tests**: Manual testing per quickstart.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration for new feature

- [x] T001 Add `extra_prompt` column migration to `ai_tasks` table in `database.py` line ~395 in `init_db_tables()` method using `_migrate_table()` helper

**Checkpoint**: Database schema updated - ready for user story implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 [P] Verify Volcengine Files API integration in `ai_utils/volc_file_manager.py` (check `upload_file()` method and API endpoint)
- [x] T003 [P] Verify Volcengine message formatting in `ai_utils/ai_helper.py` (check `call_ai_platform_chat()` supports content list format)
- [x] T004 [P] Review existing glassmorphic design system in `templates/base.html` (identify `.glass-panel`, `.glass-input`, focus state classes)
- [x] T005 [P] Review existing `_migrate_table()` pattern in `database.py` lines 419-429 (understand migration helper method)
- [x] T006 [P] Review current message structure bug in `grading_core/direct_grader_template.py` lines 148-154 (document incorrect format)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 2 - Fix Volcengine Multimodal Integration (Priority: P0) 🚨 CRITICAL BUG FIX

**Goal**: Fix AI direct cores to properly handle images (base64), videos (Files API), and PDFs (Files API)

**Independent Test**: Create a new AI direct core and run it against student submissions containing:
- Image files (PNG/JPG) → Should convert to base64 and process successfully
- Video files (MP4) → Should upload via Files API and process successfully
- PDF files → Should upload via Files API and process successfully
- Mixed media (images + videos + code) → All file types handled correctly

### Research & Analysis for User Story 2

- [x] T007 [P] [US2] Read `ai_utils/ARC_doc.md` to understand Volcengine Responses API content list format requirements
- [x] T008 [P] [US2] Analyze correct content list format: `[{"type": "input_text", "text": "..."}, {"type": "input_image", "image_url": {"url": "data:image/png;base64,..."}}]`
- [x] T009 [P] [US2] Identify supported image formats: JPG, PNG, JPEG, GIF, WebP, BMP, TIFF, HEIC (per research.md)
- [x] T010 [P] [US2] Identify supported video formats: MP4, AVI, MOV (per research.md)
- [x] T011 [P] [US2] Confirm file size limit: 512 MB per file (per Volcengine documentation)

### Implementation for User Story 2

#### File Processing Logic

- [x] T012 [P] [US2] Add file size check (512 MB limit) before processing in `grading_core/direct_grader_template.py` grade() method
- [x] T013 [P] [US2] Add file size warning log when file exceeds limit in `grading_core/direct_grader_template.py`
- [x] T014 [P] [US2] Add skip logic for oversized files with `continue` statement in `grading_core/direct_grader_template.py`
- [x] T015 [P] [US2] Add media file counter initialization in `grading_core/direct_grader_template.py` grade() method
- [x] T016 [P] [US2] Add soft limit check (5 files) with warning in `grading_core/direct_grader_template.py`
- [x] T017 [P] [US2] Add hard limit check (10 files) with early return in `grading_core/direct_grader_template.py`
- [x] T018 [P] [US2] Define constants: `MAX_MEDIA_FILES = 10`, `SOFT_MEDIA_LIMIT = 5`, `MAX_FILE_SIZE = 512 * 1024 * 1024` in `grading_core/direct_grader_template.py`

#### Image Processing (Base64 Encoding)

- [x] T019 [P] [US2] Add image file extension check for `.jpg`, `.png`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.tiff`, `.heic` in `grading_core/direct_grader_template.py`
- [x] T020 [P] [US2] Implement base64 encoding for images using `base64.b64encode()` in `grading_core/direct_grader_template.py`
- [x] T021 [P] [US2] Implement MIME type detection for images using `mimetypes.guess_type()` in `grading_core/direct_grader_template.py`
- [x] T022 [P] [US2] Format base64 image as data URL: `f"data:{mime_type};base64,{b64_str}"` in `grading_core/direct_grader_template.py`
- [x] T023 [P] [US2] Construct content list item for image: `{"type": "input_image", "image_url": {"url": data_url}}` in `grading_core/direct_grader_template.py`
- [x] T024 [P] [US2] Add success log after image encoding: `print(f"[Grader] 图片已编码: {filename}")` in `grading_core/direct_grader_template.py`

#### Video Processing (Files API Upload)

- [x] T025 [P] [US2] Add video file extension check for `.mp4`, `.avi`, `.mov` in `grading_core/direct_grader_template.py`
- [x] T026 [P] [US2] Initialize `VolcFileManager` instance if videos/PDFs detected in `grading_core/direct_grader_template.py` grade() method
- [x] T027 [P] [US2] Call `VolcFileManager.upload_file(video_path)` for videos in `grading_core/direct_grader_template.py`
- [x] T028 [P] [US2] Construct content list item for video: `{"type": "input_file", "file_id": fid}` in `grading_core/direct_grader_template.py`
- [x] T029 [P] [US2] Add success log after video upload: `print(f"[Grader] 视频文件已上传: {filename} -> {fid}")` in `grading_core/direct_grader_template.py`
- [x] T030 [P] [US2] Add error handling for failed video uploads with `try/except` in `grading_core/direct_grader_template.py`
- [x] T031 [P] [US2] Add deduction log when video upload fails: `self.res.add_deduction(f"视频文件处理失败: {filename}")` in `grading_core/direct_grader_template.py`

#### PDF Processing (Files API Upload)

- [x] T032 [P] [US2] Add PDF file extension check for `.pdf` in `grading_core/direct_grader_template.py`
- [x] T033 [P] [US2] Call `VolcFileManager.upload_file(pdf_path)` for PDFs in `grading_core/direct_grader_template.py`
- [x] T034 [P] [US2] Construct content list item for PDF: `{"type": "input_file", "file_id": fid}` in `grading_core/direct_grader_template.py`
- [x] T035 [P] [US2] Add success log after PDF upload: `print(f"[Grader] PDF文件已上传: {filename} -> {fid}")` in `grading_core/direct_grader_template.py`
- [x] T036 [P] [US2] Add error handling for failed PDF uploads with `try/except` in `grading_core/direct_grader_template.py`
- [x] T037 [P] [US2] Add deduction log when PDF upload fails: `self.res.add_deduction(f"PDF文件处理失败: {filename}")` in `grading_core/direct_grader_template.py`

#### Message Structure & Text Processing

- [x] T038 [US2] Initialize `content_list = []` before file processing in `grading_core/direct_grader_template.py` grade() method
- [x] T039 [US2] Add text content to `content_list` as `{"type": "input_text", "text": user_content}` in `grading_core/direct_grader_template.py`
- [x] T040 [US2] Remove incorrect `file_ids` field from message structure in `grading_core/direct_grader_template.py` (old bug)
- [x] T041 [US2] Replace string `content` with list `content: content_list` in `grading_core/direct_grader_template.py` message construction
- [x] T042 [US2] Update message structure to: `messages = [{"role": "user", "content": content_list}]` in `grading_core/direct_grader_template.py`

#### Error Handling & Resilience

- [x] T043 [US2] Wrap file processing in `try/except` to catch encoding errors in `grading_core/direct_grader_template.py`
- [x] T044 [US2] Add `continue` statement after file processing errors to proceed with remaining files in `grading_core/direct_grader_template.py`
- [x] T045 [US2] Add error log with traceback: `traceback.print_exc()` for debugging in `grading_core/direct_grader_template.py`
- [x] T046 [US2] Add check for empty `content_list` before AI call with appropriate error message in `grading_core/direct_grader_template.py`
- [x] T047 [US2] Ensure `VolcFileManager` is only initialized when needed (if videos/PDFs exist) in `grading_core/direct_grader_template.py`

**Checkpoint**: AI direct cores now properly handle images (base64), videos (Files API), and PDFs (Files API) without runtime errors

---

## Phase 4: User Story 1 - Add Extra Prompt to Logic Core Generator (Priority: P1) 🎯 HIGH VALUE FEATURE

**Goal**: Add extra prompt textarea to AI generator page, allowing teachers to provide additional guidance (e.g., file matching flexibility) when generating logic cores

**Independent Test**:
1. Visit `/ai_generator` page
2. Fill form with exam/standard files
3. Enter extra prompt: "Consider common typos in filenames like test1.py vs test01.py"
4. Submit and verify generated grader includes flexible file matching patterns

### Database Layer for User Story 1

- [x] T048 [P] [US1] Update `insert_ai_task()` method signature in `database.py` to accept `extra_prompt` parameter
- [x] T049 [P] [US1] Add `extra_prompt` parameter to SQL INSERT statement in `database.py` `insert_ai_task()` method
- [x] T050 [P] [US1] Update `get_ai_task()` method (if exists) to return `extra_prompt` field in `database.py`
- [x] T051 [P] [US1] Verify `extra_prompt` column default value is `''` (empty string) for backward compatibility in `database.py`

### Backend Blueprint for User Story 1

- [x] T052 [P] [US1] Extract `extra_prompt` from form data using `request.form.get('extra_prompt', '')` in `blueprints/ai_generator.py` create_task() route
- [x] T053 [P] [US1] Pass `extra_prompt` to `db.insert_ai_task()` call in `blueprints/ai_generator.py` create_task() route (line ~138)
- [x] T054 [P] [US1] Add `extra_prompt` to worker thread args list in `blueprints/ai_generator.py` create_task() route (line ~146)
- [x] T055 [P] [US1] Verify `extra_prompt` is passed as parameter after `max_score` and before `app_config` in `blueprints/ai_generator.py`

### Service Layer for User Story 1

- [x] T056 [P] [US1] Update `generate_grader_worker()` function signature to accept `extra_prompt` parameter in `services/ai_service.py` (line ~174)
- [x] T057 [P] [US1] Add `extra_prompt` parameter after `extra_desc` and before `max_score` in `services/ai_service.py` function signature
- [x] T058 [P] [US1] Build prompt section for extra prompt: `if extra_prompt: prompt_parts.append(f"### 6. 额外生成提示\n{extra_prompt}")` in `services/ai_service.py`
- [x] T059 [P] [US1] Integrate extra prompt into final prompt construction after `extra_desc` section in `services/ai_service.py` (line ~206)
- [x] T060 [P] [US1] Ensure extra prompt is included in AI generation payload at `services/ai_service.py` line ~217

### Frontend HTML for User Story 1

- [x] T061 [P] [US1] Add container div for extra prompt input with `md:col-span-2` class in `templates/components/form_logic.html` (after extra_desc field, around line ~107)
- [x] T062 [P] [US1] Add label with icon: `<i class="fas fa-lightbulb mr-1 text-amber-500"></i>` for extra prompt in `templates/components/form_logic.html`
- [x] T063 [P] [US1] Add character counter element: `<span id="extraPromptCounter">0 / 2000</span>` in label area in `templates/components/form_logic.html`
- [x] T064 [P] [US1] Add textarea with `name="extra_prompt"`, `id="extra_prompt"`, `rows="4"`, `maxlength="5000"` in `templates/components/form_logic.html`
- [x] T065 [P] [US1] Add glassmorphic classes to textarea: `.glass-panel`, `bg-white/50`, `backdrop-blur` in `templates/components/form_logic.html`
- [x] T066 [P] [US1] Add focus state classes: `focus:outline-none`, `focus:bg-white`, `focus:border-indigo-400` in `templates/components/form_logic.html`
- [x] T067 [P] [US1] Add placeholder with examples (file matching typos, PDF handling, etc.) in `templates/components/form_logic.html` textarea
- [x] T068 [P] [US1] Add `oninput="updateExtraPromptCounter(this)"` event handler to textarea in `templates/components/form_logic.html`
- [x] T069 [P] [US1] Add warning banner div: `id="extraPromptWarning"`, hidden by default, with amber styling in `templates/components/form_logic.html`
- [x] T070 [P] [US1] Add warning text: "提示词超过 2000 字符，可能增加 Token 消费。建议精简内容。" in warning banner in `templates/components/form_logic.html`
- [x] T071 [P] [US1] Add regeneration support: populate extra prompt from `ref_task['extra_prompt']` if regenerating in `templates/components/form_logic.html`

### Frontend JavaScript for User Story 1

- [x] T072 [P] [US1] Implement `updateExtraPromptCounter(textarea)` function in `templates/components/gen_form_scripts.html`
- [x] T073 [P] [US1] Get character count: `const count = textarea.value.length` in `updateExtraPromptCounter()` function
- [x] T074 [P] [US1] Update counter text: `counter.textContent = \`${count} / ${limit}\`` in `updateExtraPromptCounter()` function
- [x] T075 [P] [US1] Add warning threshold check: `if (count > limit)` in `updateExtraPromptCounter()` function
- [x] T076 [P] [US1] Add warning color class: `counter.classList.add('text-amber-600', 'font-bold')` when exceeded in `updateExtraPromptCounter()`
- [x] T077 [P] [US1] Show warning banner: `warning.classList.remove('hidden')` when exceeded in `updateExtraPromptCounter()` function
- [x] T078 [P] [US1] Remove warning classes when under limit: `counter.classList.remove('text-amber-600', 'font-bold')` in `updateExtraPromptCounter()`
- [x] T079 [P] [US1] Hide warning banner when under limit: `warning.classList.add('hidden')` in `updateExtraPromptCounter()` function
- [x] T080 [US1] Add DOMContentLoaded event listener to initialize counter on page load in `templates/components/gen_form_scripts.html`
- [x] T081 [US1] Call `updateExtraPromptCounter(extraPrompt)` on page load to set initial count in `templates/components/gen_form_scripts.html`

**Checkpoint**: Teachers can now provide extra prompts when generating logic cores, and the generated code reflects the additional guidance

---

## Phase 5: User Story 3 - Maintain Visual Consistency with Glassmorphic Design (Priority: P2)

**Goal**: Ensure the new extra prompt textarea matches the existing glassmorphic design system

**Independent Test**: Visually inspect the AI generator page to ensure:
- Extra prompt textarea uses `.glass-panel` class with backdrop blur
- Background is semi-transparent (`bg-white/50`)
- Focus states match other inputs (border color change, shadow)
- Padding and border-radius are consistent

### Verification Tasks for User Story 3

- [x] T082 [P] [US3] Verify extra prompt textarea uses `.glass-panel` class in `templates/components/form_logic.html` (from US1 T065)
- [x] T083 [P] [US3] Verify extra prompt textarea has `bg-white/50` background in `templates/components/form_logic.html` (from US1 T065)
- [x] T084 [P] [US3] Verify extra prompt textarea has consistent padding: `p-4` or `px-4 py-3` in `templates/components/form_logic.html` (from US1 T065)
- [x] T085 [P] [US3] Verify extra prompt textarea has consistent border-radius: `rounded-xl` or `rounded-lg` in `templates/components/form_logic.html` (from US1 T065)
- [x] T086 [US3] Verify extra prompt textarea has focus ring: `focus:ring-4`, `focus:ring-indigo-500/10` in `templates/components/form_logic.html` (from US1 T065)
- [x] T087 [US3] Verify extra prompt textarea has border color change on focus: `focus:border-indigo-400` in `templates/components/form_logic.html` (from US1 T065)
- [x] T088 [US3] Verify character counter uses consistent typography: `text-xs`, `text-slate-400` in `templates/components/form_logic.html` (from US1 T063)
- [x] T089 [US3] Verify warning banner uses amber color scheme: `bg-amber-50`, `border-amber-200`, `text-amber-600` in `templates/components/form_logic.html` (from US1 T069)
- [x] T090 [US3] Compare extra prompt textarea styling with existing `extra_instruction` textarea for consistency in `templates/components/form_logic.html`
- [x] T091 [US3] Verify label uses consistent styling: `text-xs font-bold text-slate-500 uppercase tracking-wider` in `templates/components/form_logic.html` (from US1 T062)

**Note**: These verification tasks ensure the implementation from US1 (T061-T081) follows the design system. They verify the frontend implementation matches the glassmorphic design requirements.

**Checkpoint**: Extra prompt textarea is visually consistent with the glassmorphic design system

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and completion tasks

### Documentation Updates

- [x] T092 [P] Update CLAUDE.md to document `extra_prompt` parameter in the AI generation section
- [x] T093 [P] Add inline comment explaining Volcengine content list format in `grading_core/direct_grader_template.py` (around message construction)
- [x] T094 [P] Add inline comment explaining hybrid approach: base64 for images, Files API for videos/PDFs in `grading_core/direct_grader_template.py`
- [x] T095 [P] Add inline comment for character limit soft limit behavior in `templates/components/gen_form_scripts.html`

### Backward Compatibility Verification

- [x] T096 [P] Test logic core generation with empty extra prompt field in `/ai_generator` page (verify backward compatibility)
- [x] T097 [P] Test AI direct core creation with only images (no videos/PDFs) to verify no regression
- [x] T098 [P] Test AI direct core creation with only videos (no images/PDFs) to verify no regression
- [x] T099 [P] Test AI direct core creation with only PDFs (no images/videos) to verify no regression
- [x] T100 [P] Verify existing graders (created before this feature) still load and run correctly

### Existing Functionality Preservation

- [x] T101 [P] Verify grader creation (logic and direct) still works from `/ai_generator` page
- [x] T102 [P] Verify grader listing works in `/ai_core_list` page
- [x] T103 [P] Verify grader deletion works (graders can be moved to trash)
- [x] T104 [P] Verify grader code viewing works (clicking on grader shows code)
- [x] T105 [P] Verify class creation and student list upload still work
- [x] T106 [P] Verify ZIP file extraction for student submissions still works

### Manual Testing & Validation

- [ ] T107 [P] **Manual Test**: Create logic core with extra prompt about file name variations and verify flexible matching in generated code
- [ ] T108 [P] **Manual Test**: Create logic core with empty extra prompt and verify it works as before (backward compatibility)
- [ ] T109 [P] **Manual Test**: Create AI direct core and test with student submission containing PNG/JPG images
- [ ] T110 [P] **Manual Test**: Create AI direct core and test with student submission containing MP4 videos
- [ ] T111 [P] **Manual Test**: Create AI direct core and test with student submission containing PDF files
- [ ] T112 [P] **Manual Test**: Create AI direct core and test with mixed media submission (images + videos + code)
- [ ] T113 [P] **Manual Test**: Create AI direct core and test with oversized file (>512 MB) to verify skip behavior
- [ ] T114 [P] **Manual Test**: Create AI direct core and test with 11 media files to verify hard limit rejection
- [ ] T115 [P] **Manual Test**: Verify character counter updates correctly when typing in extra prompt field
- [ ] T116 [P] **Manual Test**: Verify warning banner appears when extra prompt exceeds 2000 characters
- [ ] T117 [P] **Manual Test**: Run complete workflow from quickstart.md for logic core with extra prompt
- [ ] T118 [P] **Manual Test**: Run complete workflow from quickstart.md for AI direct core with mixed media

### Optional Tasks

- [ ] T119 [P] Regenerate existing AI direct cores to use fixed template (optional, manual process - requires identifying affected cores and regenerating via UI)
- [ ] T120 Document any known issues or edge cases in project README or documentation (if discovered during testing)

**Checkpoint**: Feature complete with documentation, backward compatibility verified, and manual testing complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: No dependencies - verification tasks can run in parallel
- **User Story 2 (Phase 3 - P0)**: Can start after Foundational (Phase 2) - **BLOCKING BUG, HIGHEST PRIORITY**
- **User Story 1 (Phase 4 - P1)**: Can start after Foundational (Phase 2) - **HIGH VALUE**
- **User Story 3 (Phase 5 - P2)**: Can start after User Story 1 implementation (verifies US1 frontend styling)
- **Polish (Phase 6)**: Depends on US1 and US2 being complete

### Recommended Execution Order

**Option 1: Bug Fix First (Recommended)**
1. Phase 1: Setup → T001 (database migration)
2. Phase 2: Foundational → T002-T006 (understand codebase)
3. Phase 3: US2 (P0) → T007-T047 (fix blocking multimodal bug)
4. **STOP & VALIDATE**: Test AI direct cores with images/videos/PDFs (T109-T114)
5. Phase 4: US1 (P1) → T048-T081 (add extra prompt feature)
6. **STOP & VALIDATE**: Test logic core generation with extra prompts (T107-T108, T115-T116)
7. Phase 5: US3 (P2) → T082-T091 (verify visual consistency - done as part of US1)
8. Phase 6: Polish → T092-T120 (documentation and validation)
9. **DEPLOY**: Both critical bug and high-value feature delivered

**Option 2: Feature First (If bug is not immediately blocking)**
1. Phase 1: Setup → T001
2. Phase 2: Foundational → T002-T006
3. Phase 4: US1 (P1) → T048-T081 (high value, low risk)
4. **STOP & VALIDATE**: Test logic core generation with extra prompts (T107-T108)
5. Phase 3: US2 (P0) → T007-T047 (fix blocking multimodal bug)
6. **STOP & VALIDATE**: Test AI direct cores with images/videos/PDFs (T109-T114)
7. Phase 5: US3 (P2) → T082-T091
8. Phase 6: Polish → T092-T120
9. **DEPLOY**: Both features delivered

### User Story Dependencies

- **User Story 2 (P0)**: Independent - can start after Foundational phase, no dependencies on US1
- **User Story 1 (P1)**: Independent - can start after Foundational phase, no dependencies on US2
- **User Story 3 (P2)**: Depends on User Story 1 - verifies US1 frontend implementation follows design system

### Within Each User Story

**User Story 2 (Fix Volcengine Multimodal)**:
- T007-T011 (Research & Analysis) can run in parallel (5 tasks)
- T012-T018 (File Processing Logic) can run in parallel (7 tasks)
- T019-T024 (Image Processing) can run in parallel (6 tasks)
- T025-T031 (Video Processing) can run in parallel (7 tasks)
- T032-T037 (PDF Processing) can run in parallel (6 tasks)
- T038-T047 (Message Structure & Error Handling) - T038-T042 must be sequential, T043-T047 can run in parallel

**User Story 1 (Add Extra Prompt)**:
- T048-T051 (Database) can run in parallel (4 tasks)
- T052-T055 (Backend Blueprint) should follow sequential order
- T056-T060 (Service Layer) can run in parallel (5 tasks)
- T061-T071 (Frontend HTML) can run in parallel (11 tasks)
- T072-T081 (Frontend JavaScript) should follow sequential order (T081 depends on T072-T080)

**User Story 3 (Visual Consistency)**:
- T082-T091 (Verification) can run in parallel (10 tasks)

### Parallel Opportunities

- **Phase 1**: T001 (single task)
- **Phase 2**: T002-T006 can all run in parallel (5 verification tasks)
- **Phase 3 (US2)**:
  - T007-T011 (5 tasks) can run in parallel
  - T012-T018 (7 tasks) can run in parallel
  - T019-T024 (6 tasks) can run in parallel
  - T025-T031 (7 tasks) can run in parallel
  - T032-T037 (6 tasks) can run in parallel
- **Phase 4 (US1)**:
  - T048-T051 (4 tasks) can run in parallel
  - T052-T055 (4 tasks) - some sequential dependency
  - T056-T060 (5 tasks) can run in parallel
  - T061-T071 (11 tasks) can run in parallel
- **Phase 5 (US3)**: T082-T091 (10 tasks) can run in parallel
- **Phase 6**: T092-T106 (15 tasks) can run in parallel, T107-T120 (14 tasks) are manual tests

---

## Parallel Example: User Story 2 (Fix Volcengine Multimodal)

```bash
# Launch all research & analysis tasks together:
Task T007: "Read ai_utils/ARC_doc.md to understand Volcengine Responses API"
Task T008: "Analyze correct content list format requirements"
Task T009: "Identify supported image formats"
Task T010: "Identify supported video formats"
Task T011: "Confirm file size limit: 512 MB"

# Launch all file processing logic tasks together:
Task T012: "Add file size check (512 MB limit)"
Task T013: "Add file size warning log"
Task T014: "Add skip logic for oversized files"
Task T015: "Add media file counter initialization"
Task T016: "Add soft limit check (5 files)"
Task T017: "Add hard limit check (10 files)"
Task T018: "Define constants for limits"

# Launch all image processing tasks together:
Task T019: "Add image file extension check"
Task T020: "Implement base64 encoding"
Task T021: "Implement MIME type detection"
Task T022: "Format base64 as data URL"
Task T023: "Construct content list item for image"
Task T024: "Add success log after encoding"

# Launch all video processing tasks together:
Task T025: "Add video file extension check"
Task T026: "Initialize VolcFileManager instance"
Task T027: "Call upload_file() for videos"
Task T028: "Construct content list item for video"
Task T029: "Add success log after upload"
Task T030: "Add error handling for uploads"
Task T031: "Add deduction log for failures"
```

---

## Parallel Example: User Story 1 (Add Extra Prompt)

```bash
# Launch all database tasks together:
Task T048: "Update insert_ai_task() method signature"
Task T049: "Add extra_prompt to SQL INSERT"
Task T050: "Update get_ai_task() to return extra_prompt"
Task T051: "Verify default value is empty string"

# Launch all service layer tasks together:
Task T056: "Update generate_grader_worker() signature"
Task T057: "Add extra_prompt to parameter list"
Task T058: "Build prompt section for extra prompt"
Task T059: "Integrate into final prompt"
Task T060: "Ensure inclusion in AI payload"

# Launch all frontend HTML tasks together:
Task T061: "Add container div for extra prompt"
Task T062: "Add label with icon"
Task T063: "Add character counter element"
Task T064: "Add textarea with attributes"
Task T065: "Add glassmorphic classes"
Task T066: "Add focus state classes"
Task T067: "Add placeholder with examples"
Task T068: "Add oninput event handler"
Task T069: "Add warning banner div"
Task T070: "Add warning text"
Task T071: "Add regeneration support"

# Then JavaScript implementation (sequential):
Task T072: "Implement updateExtraPromptCounter() function"
Task T073-T080: "Add function logic (character count, warning, etc.)"
Task T081: "Add initialization on page load"
```

---

## Implementation Strategy

### MVP First (Bug Fix + High Value Feature)

**Recommended path for maximum impact:**

1. **Phase 1: Setup** → T001 (database migration)
2. **Phase 2: Foundational** → T002-T006 (understand codebase)
3. **Phase 3: User Story 2 (P0)** → T007-T047 (fix blocking multimodal bug)
4. **STOP & VALIDATE**: Run T109-T114 (test AI direct cores with images/videos/PDFs)
5. **Phase 4: User Story 1 (P1)** → T048-T081 (add extra prompt feature)
6. **STOP & VALIDATE**: Run T107-T108, T115-T116 (test logic core generation)
7. **Phase 5: User Story 3 (P2)** → T082-T091 (verify visual consistency)
8. **Phase 6: Polish** → T092-T120 (documentation and validation)
9. **DEPLOY**: Both critical bug and high-value feature delivered

### Incremental Delivery

**If you want to deliver value incrementally:**

1. **Iteration 1 (Bug Fix)**:
   - Complete Phase 1 + Phase 2 (T001-T006)
   - Complete Phase 3: User Story 2 (T007-T047)
   - Validate: T109-T114 (manual tests)
   - **DEPLOY**: AI direct cores now work with images/videos/PDFs

2. **Iteration 2 (Feature Add)**:
   - Complete Phase 4: User Story 1 (T048-T081)
   - Validate: T107-T108, T115-T116 (manual tests)
   - **DEPLOY**: Teachers can now guide logic core generation

3. **Iteration 3 (Polish)**:
   - Complete Phase 5: User Story 3 (T082-T091)
   - Complete Phase 6: Polish (T092-T120)
   - **DEPLOY**: Feature complete with consistent design

### Parallel Team Strategy

**If working with multiple developers:**

1. **Team completes Phase 1 + Phase 2 together** (T001-T006)
2. **Once Foundational is done**:
   - **Developer A (Bug Fix)**: User Story 2 (T007-T047) → Fix multimodal bug
   - **Developer B (Feature Add)**: User Story 1 (T048-T081) → Add extra prompt
3. **After US1 complete**:
   - **Developer B**: User Story 3 (T082-T091) → Verify design
4. **Team converges**: Phase 6 (T092-T120) + validation

---

## Task Summary

**Total Tasks**: 120 tasks
- **Phase 1 (Setup)**: 1 task (completed)
- **Phase 2 (Foundational)**: 5 tasks (completed)
- **Phase 3 (US2 - Fix Volcengine)**: 41 tasks (completed)
- **Phase 4 (US1 - Extra Prompt)**: 34 tasks (completed)
- **Phase 5 (US3 - Visual Consistency)**: 10 tasks (completed)
- **Phase 6 (Polish)**: 29 tasks (11 completed, 18 pending)

**Completed**: 92/120 tasks (76.7%)
**Remaining**: 28/120 tasks (23.3%)

**Remaining Task Breakdown**:
- Documentation updates: 4 tasks (T092-T095) - completed
- Backward compatibility: 5 tasks (T096-T100) - completed
- Existing functionality: 6 tasks (T101-T106) - completed
- Manual testing: 12 tasks (T107-T118) - **pending, required**
- Optional tasks: 2 tasks (T119-T120) - **optional**

**Critical Path**: T107-T118 (manual testing) - these tasks validate the feature works correctly

---

## Notes

- **[P] tasks** = different files or independent logic, can run in parallel
- **[Story] label** = maps task to specific user story for traceability
- **US2 (P0)**: Blocking bug fix - prevents AI direct cores from working with images/videos/PDFs
- **US1 (P1)**: High-value enhancement - gives teachers more control over logic core generation
- **US3 (P2)**: Design consistency - ensures new textarea follows glassmorphic design system
- **Tasks T082-T091** verify US1 frontend implementation follows design requirements (done as part of US1)
- **Database migration (T001)** must be completed before any user story work
- **Commit after each task or logical group**
- **Stop at any checkpoint to validate story independently**
- **Manual tests (T107-T118) are critical** - they validate the feature works correctly in real scenarios
- **Backward compatibility is critical** - ensure existing cores continue to work (T096-T100)
