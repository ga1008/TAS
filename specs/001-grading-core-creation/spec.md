# Feature Specification: Grading Core Creation and Task Selection Improvements

**Feature Branch**: `001-grading-core-creation`
**Created**: 2026-02-05
**Status**: Draft
**Input**: User description: "请仔细阅读项目代码，深刻理解其中关于新建批改核心、新建批改任务的相关逻辑，完成下面的改进：1. 批改核心现有两种：由AI生成的纯逻辑批改核心和由AI直接批改的核心。两种核心生成后的名字没有统一。需要做改进：逻辑核心生成部分，将前端中的上传试卷文档、上传评分标准的框放到上面，接下来才是"试卷满分"、"批改严格度"，再下来才是"额外生成提示"，而"核心名称"可以输入也可以由AI自动生成（需要增加AI提示词并在后端解析名称），"课程名称"根据选择的试卷或评分标准中的元数据自动填入，也可以允许用户自己填写。同理，Direct AI 多模态核心的前端页面也是上面的布局和交互方式。注意改进过程不要变动视觉样式，保持页面美观。2. 新建任务页面，选择AI评分核心时，需要从数据库关联查找真正的核心名称，现在选择后显示的不是核心名称，而是 "None"、"Generic Course" 之类的，显然是错误的。请改成与"选择学生名单"的逻辑一样，从后端动态查找核心信息并填入正确的信息。3. 其他关联的逻辑的改进 4. 注意新增功能逻辑的完整性，避免半吊子工程。并且一定一定注意不要遗漏原有的其他功能"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reorganized Core Creation UI (Priority: P1)

A teacher wants to create a new grading core (either AI-generated logic core or Direct AI multimodal core). The form should follow a logical workflow: first upload the required documents (exam paper and grading criteria), then configure grading parameters (max score, strictness), then provide optional additional instructions, and finally specify the core name and course name (with intelligent defaults).

**Why this priority**: This is the most visible user-facing change that improves the core creation workflow. Reordering fields to match the mental model (documents first, then configuration, then naming) reduces user confusion and errors.

**Independent Test**: Can be fully tested by navigating to `/ai_generator` and verifying that both Logic Core and Direct AI core forms display fields in the correct order, and that file uploads work correctly.

**Acceptance Scenarios**:

1. **Given** a teacher is on the AI generator page, **When** they view the Logic Core creation form, **Then** the fields should appear in this order:
   - Upload exam document (top)
   - Upload grading criteria (second)
   - Max score (third)
   - Strictness selection (fourth)
   - Extra generation prompt (fifth)
   - Core name input (sixth, with AI auto-generation option)
   - Course name input (last, with auto-fill from metadata)

2. **Given** a teacher is on the AI generator page, **When** they switch to the Direct AI multimodal core tab, **Then** the fields should appear in the same logical order as the Logic Core form.

3. **Given** a teacher has selected exam and grading documents, **When** documents contain course metadata, **Then** the course name field should be automatically populated with the extracted course name.

4. **Given** a teacher is creating a core, **When** they click the "Auto-generate Name" button next to the core name field, **Then** the system should generate a meaningful name based on the uploaded documents (e.g., "2026年春季-数据结构与算法-期末实验").

---

### User Story 2 - AI Auto-Generation of Core Names (Priority: P2)

A teacher wants to create a grading core but doesn't want to manually type a descriptive name. The system should analyze the uploaded documents and suggest an appropriate core name.

**Why this priority**: Auto-generation reduces user effort and ensures consistent, descriptive naming conventions across cores. While not critical for functionality, it significantly improves user experience.

**Independent Test**: Can be tested by uploading documents and clicking the auto-generate button, verifying that suggested names are meaningful and based on document content.

**Acceptance Scenarios**:

1. **Given** a teacher has uploaded an exam document titled "2026春_数据结构_期末实验.pdf" and a grading criteria file, **When** they click the "Auto-generate Name" button, **Then** the system should populate the core name field with a name like "2026春-数据结构-期末实验批改核心".

2. **Given** a teacher has uploaded documents without clear naming, **When** they click the auto-generate button, **Then** the system should extract information from document content (course name, assignment type) to create a meaningful name.

3. **Given** the system has generated a core name, **When** the teacher manually edits the name, **Then** the system should accept the manual override without errors.

---

### User Story 3 - Fixed Core Selection in Task Creation (Priority: P1)

A teacher is creating a new grading task and needs to select an AI grading core. The dropdown should display the actual core names and course names from the database, not placeholder text like "None" or "Generic Course".

**Why this priority**: This is a critical bug fix. When core names display incorrectly, teachers cannot confidently select the correct core for their tasks, leading to potential errors in grading.

**Independent Test**: Can be fully tested by navigating to `/new_class`, clicking on the core selection dropdown, and verifying that all cores display with correct names and course information.

**Acceptance Scenarios**:

1. **Given** a teacher is on the new task page, **When** they click on the "选择评分标准 (AI核心)" dropdown, **Then** each option should display the actual core name stored in the database.

2. **Given** a teacher selects a core from the dropdown, **When** the selection is made, **Then** the course name field should be auto-filled with the correct course name associated with that core.

3. **Given** the database contains cores with missing course names, **When** the dropdown is rendered, **Then** it should display a fallback label like "未分类" (Uncategorized) instead of "None".

4. **Given** a teacher is viewing the core dropdown, **When** they type in the search box, **Then** the list should filter correctly based on core names and course names.

---

### User Story 4 - Unified Naming Convention Across Core Types (Priority: P2)

The system currently stores and displays core names inconsistently between AI-generated logic cores and Direct AI multimodal cores. Teachers need to see consistent naming and course information regardless of core type.

**Why this priority**: Consistency across core types makes the system more predictable and easier to use. While not blocking functionality, inconsistent naming creates confusion.

**Independent Test**: Can be verified by creating both types of cores and checking that they appear with consistent naming in the task creation dropdown.

**Acceptance Scenarios**:

1. **Given** a teacher has created both a Logic Core and a Direct AI Core, **When** they view the core selection dropdown, **Then** both cores should display with the same naming format and include course information.

2. **Given** a core is created, **When** it is saved to the database, **Then** both the `name` and `course_name` fields should be populated (not NULL or empty).

---

### Edge Cases

- When documents are uploaded without any metadata or readable content for name generation, system shows a helpful message and allows manual name entry.
- When a user manually edits an auto-generated course name after document selection, the system accepts the edit without re-validation.
- When the database contains legacy cores with NULL course names, system displays fallback label "未分类" (Uncategorized) in dropdowns.
- When file upload fails or times out during core creation, system shows error message and allows retry or alternative file selection.
- When AI service is unavailable for name generation, system shows error message but allows manual name entry (does not block form submission).
- When documents are uploaded in unsupported formats, system shows clear error message indicating supported formats.
- When a user regenerates a core from a previous task (inherit mode), system pre-fills name/course from the reference task and allows editing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST reorganize the Logic Core creation form (`templates/components/form_logic.html`) to display fields in the following order: (1) Exam document upload, (2) Grading criteria upload, (3) Max score input, (4) Strictness selection, (5) Extra generation prompt, (6) Core name input (with AI auto-generation), (7) Course name input (with auto-fill from metadata).

- **FR-002**: System MUST reorganize the Direct AI Core creation form (`templates/components/form_direct.html`) to display fields in the same logical order as the Logic Core form.

- **FR-003**: System MUST provide an AI auto-generation feature for core names that analyzes uploaded documents and suggests meaningful names following the format `[Year/Season]-[CourseName]-[AssignmentType]批改核心` based on document content, metadata, and context.

- **FR-004**: System MUST extract and auto-fill course name from document metadata (stored in `file_assets.meta_info` or `file_assets.course_name`) when both exam and grading criteria documents are selected (single batch call).

- **FR-005**: System MUST allow users to manually edit both auto-generated core names and auto-filled course names.

- **FR-006**: System MUST fix the core selection dropdown in task creation (`templates/newClass.html`) to display actual core names and course names from the database instead of "None" or "Generic Course".

- **FR-007**: System MUST populate the course name field in task creation when a core is selected, using the `course_name` associated with the selected core.

- **FR-008**: System MUST provide a fallback display label (e.g., "未分类" or "Uncategorized") for cores in the database that have NULL or empty course names.

- **FR-009**: System MUST ensure both Logic Cores and Direct AI Cores store their `name` and `course_name` in the database with consistent, non-NULL values upon creation.

- **FR-010**: System MUST update the AI prompt template to include instructions for extracting and suggesting course names from document content.

- **FR-011**: System MUST preserve all existing functionality including file modal selection, regeneration from existing tasks, strictness selection, max score configuration, and extra prompts.

- **FR-012**: System MUST maintain the current visual styling (glass-panel effects, hover states, transitions, colors) during the UI reorganization.

- **FR-013**: System SHALL provide an optional admin bulk-edit feature to update course names for legacy cores that have NULL or empty course_name values.

### Non-Functional Requirements

- **NFR-001**: System MUST log AI auto-generation requests with timestamp, outcome (success/failure), and error messages for debugging and monitoring.

- **NFR-002**: System MUST complete course name auto-fill within 3 seconds of both documents being selected.

### Key Entities

- **AI Task/Grading Core**: Represents a grading configuration with attributes including `id`, `name`, `course_name`, `grader_id`, `max_score`, `strictness`, `exam_path`, `standard_path`, and `extra_desc`. Two types exist: Logic Cores (AI generates Python scripts) and Direct AI Cores (AI grades directly).

- **File Asset**: Represents uploaded documents with attributes including `file_hash`, `original_name`, `meta_info` (JSON format with document metadata), `course_name`, `doc_category`, `academic_year`, and `semester`. Used as source material for core creation.

- **Student List**: Represents a class roster with attributes including `id`, `class_name`, `student_count`, `college`, `education_type`, and `enrollment_year`. Used in task creation alongside core selection.

- **Class/Task**: Represents a grading task that associates a core with a student list, with attributes including `id`, `name`, `course`, `strategy` (core ID), and `workspace_path`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Teachers can complete core creation with 100% of fields in the correct logical order (documents → parameters → instructions → naming) without any visual style degradation.

- **SC-002**: 90% of core names are auto-generated successfully when documents contain sufficient metadata, reducing manual typing by at least 50% based on field character count.

- **SC-003**: 80% of course names are auto-filled correctly from document metadata, measured by verification that auto-filled values match expected course names.

- **SC-004**: 100% of cores display with correct names and course information in the task creation dropdown, eliminating "None" or "Generic Course" placeholders.

- **SC-005**: Task creation completion rate improves by at least 20% due to clearer core selection (measured by comparing task creation success rates before and after the fix).

- **SC-006**: Zero regression in existing functionality - all features (file upload, regeneration, strictness, extra prompts, student list selection) continue to work as before.

- **SC-007**: Page load times for core creation and task creation pages remain under 2 seconds, measured by browser network timing.

## Clarifications

### Session 2026-02-05

- Q: When AI auto-generation fails or returns unusable results, how should the system respond? → A: Show error message but allow manual entry (user can still type their own name)
- Q: When should the system attempt to extract and populate the course name? → A: After both exam and grading criteria are selected (single batch call)
- Q: For existing cores with NULL or empty course_name values, what approach should be taken? → A: Display-only fix (fallback label) + optional admin bulk-edit feature
- Q: What format should auto-generated core names follow? → A: [Year/Season]-[CourseName]-[AssignmentType]批改核心
- Q: What level of logging/observability should be implemented for AI auto-generation? → A: Standard logging (request timestamp, outcome success/failure, error messages)

## Assumptions

1. Document metadata (`meta_info` JSON field in `file_assets` table) may contain course information, but the exact structure needs to be determined during implementation. If metadata doesn't exist, AI will analyze document content.

2. The AI service (accessible via `AI_ASSISTANT_BASE_URL`) is capable of analyzing document content and extracting key information like course name and assignment type.

3. Legacy cores in the database may have NULL or empty `course_name` values; these will be handled with fallback display labels.

4. The visual styling system (Tailwind CSS classes, custom glass-panel styles) will remain unchanged throughout the reorganization.

5. File modal selection functionality (`openFileModal`, `confirmFileSelection`) will continue to work without modification.

6. The grading core factory (`grading_core/factory.py`) returns strategy tuples that need to be enhanced with proper course information.

7. Auto-generation will be triggered by a user action (button click) rather than happening automatically, to avoid unexpected API calls.

8. The extra prompt/extra instruction fields will retain their current character limits and validation behavior.
