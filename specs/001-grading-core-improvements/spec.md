# Feature Specification: Grading Core Improvements

**Feature Branch**: `001-grading-core-improvements`
**Created**: 2026-02-03
**Status**: Draft
**Input**: User description: "请认真仔细的理解批改核心的逻辑，帮我改进批改核心的相关功能。批改核心分为逻辑核心和AI直接批改核心，区别是逻辑核心是由AI助手根据用户选择的文档生成的一个python文件，在后续用户批改作业时使用py逻辑批改作业，速度块但是准确度低；AI直接批改核心则是只生成一个提示语py文件，用户批改时，后端是直接调用AI助手来批改作业，优点是准确度高但是速度低。现在逻辑核心和AI直接核心都还有需要改进的地方。具体要求如下：
1. 逻辑核心现在只能选择宽松度，需要加上用户的额外提示，例如让AI在生成匹配文件名逻辑时把学生可能漏写、错写文件名的情况也考虑进去，避免错过学生提交的文件等等。增加的额外提示的实现：后端部分需要添加到给生成逻辑核心的AI的提示中去，前端部分需要在原有的布局上添加一个输入框（合理的布局和合理的大小，以及注意交互）。
2. AI核心现在能生成一个批改核心，但是运行的时候却是报错的。由于现在的AI核心使用的是火山引擎的多模态模型（可以识别图片、视频文字等信息），需要仔细阅读ai_utils\ARC_doc.md 文件，确认现在的火山引擎的AI核心的使用逻辑是否符合文档要求。根据以往经验，图片文件一般是转换为base64然后跟随其他文字输入传给AI才能成功处理。由于学生上传的文件的不确定性，需要将所有能识别的文件都使用这种方式传给火山引擎AI，让它以处理base64的方式处理学生的提交（注意后端先识别合理的文件才上传，避免上传无用的文件或太大的文件）
3. 注意在改进过程不要遗漏原有的其他功能
4. 注意前端的美观性"

---

## Clarifications

### Session 2026-02-03

- Q: When file encoding or upload fails (FR-011: "handle errors gracefully"), what specific behavior should occur? → A: Skip failed files, log warnings, continue grading with remaining files
- Q: FR-012 mentions a "recommended: 5 files" limit per submission. Is this a hard or soft limit, and what happens when exceeded? → A: Soft limit with user override, 10-file hard maximum
- Q: For images (FR-006/FR-007), should the system use base64 encoding OR upload via Volcengine Files API like videos/PDFs? → A: Use base64 encoding for images only, Files API for videos/PDFs (hybrid approach)
- Q: When extra prompt input exceeds the recommended 2000 character limit (FR-005), what should happen? → A: Show warning but allow submission (soft limit)
- Q: When student submission files exceed the 512 MB Volcengine limit, what should happen? → A: Skip file with warning, continue grading with remaining files

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Extra Prompt to Logic Core Generator (Priority: P1)

**Why this priority**: This is a high-value, low-risk enhancement that directly addresses a user pain point. Teachers need more control over how AI generates file-matching logic to reduce false negatives when students submit files with naming variations.

**Independent Test**: Can be fully tested by generating a new logic core with an extra prompt (e.g., "Consider common typos in filenames like 'test1.py' vs 'test01.py'") and verifying that the generated Python code includes flexible file matching patterns.

**Acceptance Scenarios**:

1. **Given** a teacher is on the AI generator page with exam and rubric files selected, **When** they enter text in the new "Extra Prompt" textarea describing file matching considerations, **Then** the prompt text should be included in the AI generation request and reflected in the generated grader code.

2. **Given** a teacher enters extra instructions about handling filename variations, **When** the logic core is generated and used to grade student submissions, **Then** the grader should demonstrate more flexible file matching (e.g., finding "test01.py" when looking for "test1.py").

3. **Given** a teacher leaves the extra prompt field empty, **When** they submit the form, **Then** the system should generate the grader using default behavior (backward compatibility).

---

### User Story 2 - Fix Volcengine Multimodal Integration for AI Direct Core (Priority: P0)

**Why this priority**: This is a blocking bug fix. The AI direct core currently fails at runtime when processing student submissions containing images, videos, or PDFs. This prevents a core feature from working entirely.

**Independent Test**: Can be fully tested by creating a new AI direct core and running it against student submissions containing images (PNG/JPG), videos (MP4), and PDFs. The grader should successfully process these files without errors and return valid scores.

**Acceptance Scenarios**:

1. **Given** a teacher creates an AI direct grader, **When** students submit assignments containing image files (JPG, PNG), **Then** the system should convert images to base64 and successfully send them to the Volcengine AI model for grading without errors.

2. **Given** a teacher creates an AI direct grader, **When** students submit assignments containing video files (MP4, AVI, MOV), **Then** the system should upload videos via Volcengine Files API and pass the file_id to the AI model for processing.

3. **Given** a teacher creates an AI direct grader, **When** students submit assignments containing PDF files, **Then** the system should upload PDFs via Volcengine Files API and pass the file_id to the AI model.

4. **Given** student submissions contain mixed media types (images + videos + code files), **When** the AI direct grader processes the submission, **Then** all supported file types should be correctly handled and the AI should return a valid JSON response with scores and feedback.

---

### User Story 3 - Maintain Visual Consistency with Glassmorphic Design (Priority: P2)

**Why this priority**: Visual consistency is important for user experience and system credibility, but this is lower priority than fixing the blocking bug and adding the extra prompt feature.

**Independent Test**: Can be verified by visually inspecting the AI generator page to ensure the new extra prompt textarea matches the existing glassmorphic design system.

**Acceptance Scenarios**:

1. **Given** a teacher views the AI generator page, **When** they see the new "Extra Prompt" input field, **Then** it should use the same `.glass-panel` styling with backdrop blur, semi-transparent background (`bg-white/50`), and consistent padding/border-radius as other form elements.

2. **Given** a teacher interacts with the extra prompt textarea, **When** they focus on the field, **Then** it should display the same focus state visual effects (border color change, subtle shadow) as other inputs on the page.

---

### Edge Cases

- **Resolved**: Extra prompts with special characters, quotes, or multi-line text are properly escaped and handled during AI generation (FR-002).
- **Resolved**: Files exceeding 512 MB are skipped with a warning, and grading continues with remaining files (FR-010).
- **How does system handle** when Volcengine returns non-JSON responses or malformed data?
- **How does system handle** when no AI model with "vision" capability is configured?
- **Resolved**: File encoding/upload failures result in skipping the failed file, logging warnings, and continuing with remaining files (FR-011).
- **Resolved**: Extra prompts exceeding 2000 characters trigger a warning but allow submission (FR-005).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a textarea input field on the AI generator page for teachers to enter extra prompts when generating logic cores.

- **FR-002**: System MUST include the extra prompt content in the AI request when generating logic core Python code.

- **FR-003**: System MUST store the extra prompt in the database for reference and reusability.

- **FR-004**: System MUST support empty extra prompts (backward compatibility with existing behavior).

- **FR-005**: System MUST validate extra prompt input length with a soft limit of 2000 characters. When exceeded, display a warning about increased token usage but allow submission.

- **FR-006**: System MUST fix the AI direct core to properly handle image files by converting them to base64 format.

- **FR-007**: System MUST properly format base64 image data as `data:<mime-type>;base64,<base64-string>` for transmission to Volcengine.

- **FR-008**: System MUST upload video files (MP4, AVI, MOV) via Volcengine Files API and use the returned file_id.

- **FR-009**: System MUST upload PDF files via Volcengine Files API and use the returned file_id.

- **FR-010**: System MUST filter out unsupported files and files exceeding 512 MB before processing. For oversized files, log a warning and continue grading with remaining files.

- **FR-011**: When file encoding or upload fails, system MUST skip the failed file, log a warning with the error details, and continue grading with the remaining files.

- **FR-012**: System MUST enforce a soft limit of 5 media files per submission with a user warning, and a hard maximum of 10 files.

- **FR-013**: The extra prompt textarea MUST use glassmorphic design consistent with the existing frontend design system.

- **FR-014**: All form inputs MUST maintain consistent styling, spacing, and interaction patterns (hover, focus, active states).

- **FR-015**: System MUST preserve all existing functionality (logic core generation, AI direct core creation, grader deletion, etc.) during these improvements.

### Key Entities

- **Logic Core**: AI-generated Python grader that uses code-based logic to evaluate student submissions. Contains extra_prompt field for additional generation instructions.

- **AI Direct Core**: AI-generated grader that calls Volcengine multimodal model at runtime to evaluate submissions. Contains references to exam content, grading standards, and extra instructions.

- **Extra Prompt**: User-provided text input that guides AI generation behavior, particularly for file matching and edge case handling.

- **File Upload Record**: Temporary record of files uploaded to Volcengine via Files API, containing file_id, mime_type, and expiration information.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Teachers can successfully generate logic cores with extra prompts, and 100% of generated cores include the specified extra instructions.

- **SC-002**: AI direct cores successfully process student submissions containing images, videos, and PDFs without runtime errors in 95%+ of cases.

- **SC-003**: File size filtering prevents upload of files larger than 512 MB, reducing unnecessary API calls and costs.

- **SC-004**: The extra prompt input field is visually consistent with the existing glassmorphic design system (validated by visual inspection).

- **SC-005**: All existing grader functionality (create, delete, list, grade) continues to work without regression after these changes.

- **SC-006**: AI direct core grading completes within 60 seconds for typical submissions (5 media files + text content) and within 120 seconds for submissions up to the 10-file hard limit.

---

## Assumptions

1. **Volcengine API Availability**: The Volcengine Files API is available and properly configured with valid API credentials.

2. **File Type Support**: Volcengine multimodal model supports image formats (JPG, PNG, JPEG, GIF, WebP, BMP, TIFF, HEIC), video formats (MP4, AVI, MOV), and PDF files as documented in ARC_doc.md.

3. **Network Reliability**: File uploads to Volcengine will typically succeed within a reasonable timeout period (60 seconds per file).

4. **Base64 Encoding**: Images use base64 encoding for transmission; videos and PDFs use Volcengine Files API with file_id references.

5. **Teacher Intent**: The "extra prompt" is intended to provide guidance on file matching flexibility and edge case handling, not to completely rewrite the grading logic.

6. **File Limits**: The 512 MB file size limit and 20 GB total storage limit mentioned in Volcengine documentation are acceptable constraints for the system.

7. **Backward Compatibility**: Existing graders without extra prompts should continue to work without modification.
