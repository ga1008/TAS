# Data Model: Grading Core Creation and Task Selection Improvements

**Feature**: Grading Core Creation and Task Selection Improvements
**Date**: 2026-02-05
**Status**: Phase 1 - Design Artifact

## Overview

This feature does not require database schema changes. It leverages existing tables and adds new API endpoints for metadata extraction. The primary data model changes are in how data is queried and displayed.

## Existing Entities

### AI Task (Grading Core)

**Table**: `ai_tasks`

**Primary Key**: `id` (INTEGER)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | Primary key | Auto-increment |
| `name` | TEXT | Core display name | **FR-003**: Format: `[Year/Season]-[CourseName]-[AssignmentType]批改核心` |
| `course_name` | TEXT | Associated course name | **FR-009**: Must be non-NULL on creation |
| `grader_id` | TEXT | Grader class ID | Maps to `BaseGrader.ID` |
| `max_score` | INTEGER | Maximum possible score | Default: 100 |
| `strictness` | TEXT | Grading strictness | Values: 'loose', 'standard', 'strict' |
| `exam_path` | TEXT | Path to exam document | File reference |
| `standard_path` | TEXT | Path to grading criteria | File reference |
| `extra_desc` | TEXT | Additional instructions | User-provided prompts |
| `status` | TEXT | Processing status | 'pending', 'processing', 'completed', 'failed' |
| `log_info` | TEXT | Processing logs | JSON format |
| `created_by` | INTEGER | Creator user ID | Foreign key to `users.id` |
| `created_at` | TIMESTAMP | Creation timestamp | Auto-generated |

**Relationships**:
- One `ai_task` → One `grader` class (via `grader_id`)
- One `ai_task` → One `file_asset` (exam, via `exam_path`)
- One `ai_task` → One `file_asset` (criteria, via `standard_path`)

---

### File Asset

**Table**: `file_assets`

**Primary Key**: `id` (INTEGER), `file_hash` (TEXT, unique)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | Primary key | Auto-increment |
| `file_hash` | TEXT | SHA256 hash | Unique identifier |
| `original_name` | TEXT | Original filename | For display |
| `file_size` | INTEGER | File size in bytes | |
| `physical_path` | TEXT | Disk storage path | |
| `parsed_content` | TEXT | AI-extracted text | Document content |
| `meta_info` | TEXT | Document metadata | **JSON format** - contains page count, author, etc. |
| `course_name` | TEXT | Extracted course name | **FR-004**: Source for auto-fill |
| `doc_category` | TEXT | Document type | 'exam', 'course_material', etc. |
| `academic_year` | TEXT | Academic year | e.g., '2023-2024' |
| `semester` | TEXT | Semester | 'Fall', 'Spring', etc. |
| `cohort_tag` | TEXT | Batch identifier | e.g., '2401', '240' |
| `version` | INTEGER | Record version | Default: 1 |
| `uploaded_by` | INTEGER | Uploader user ID | Foreign key to `users.id` |
| `created_at` | TIMESTAMP | Upload timestamp | Auto-generated |

**meta_info JSON Structure** (example):
```json
{
  "page_count": 12,
  "author": "张三",
  "department": "计算机学院",
  "year": 2026,
  "season": "春季",
  "exam_type": "期末考试"
}
```

**Relationships**:
- One `file_asset` → Many `ai_tasks` (can be reused across cores)

---

### Class (Task)

**Table**: `classes`

**Primary Key**: `id` (INTEGER)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | Primary key | Auto-increment |
| `name` | TEXT | Class/task name | User-provided |
| `course` | TEXT | Course name | **FR-007**: Auto-filled from selected core |
| `strategy` | TEXT | Grading core ID | References `ai_tasks.grader_id` |
| `workspace_path` | TEXT | Workspace directory | Student submissions |
| `created_by` | INTEGER | Creator user ID | |
| `created_at` | TIMESTAMP | Creation timestamp | |

**Relationships**:
- One `class` → One `ai_task` (via `strategy` = `grader_id`)
- One `class` → Many `students`

---

## New API Endpoints

### POST /api/ai/generate_name

Generate a core name from selected documents.

**Request**:
```json
{
  "exam_file_id": "abc123",
  "standard_file_id": "def456"
}
```

**Response**:
```json
{
  "status": "success",
  "name": "2026春-数据结构-期末实验批改核心",
  "confidence": 0.95
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "AI service unavailable",
  "fallback_allowed": true
}
```

---

### POST /api/ai/extract_course

Extract course name from selected documents.

**Request**:
```json
{
  "exam_file_id": "abc123",
  "standard_file_id": "def456"
}
```

**Response**:
```json
{
  "status": "success",
  "course_name": "数据结构与算法",
  "source": "metadata"  // or "ai_analysis"
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "Unable to extract course name",
  "fallback_allowed": true
}
```

---

### GET /api/strategies (Enhanced)

Returns all available grading cores with proper course names.

**Current Response** (problematic):
```json
[
  ["linux_final_2026_std", "Linux Final Exam", null],
  ["direct_9fa38898", "Generic Course", "None"]
]
```

**Enhanced Response**:
```json
[
  ["linux_final_2026_std", "Linux期末批改核心", "Linux系统编程"],
  ["direct_9fa38898", "视频作业批改核心", "未分类"]
]
```

**Backend Change**: In `grading_core/factory.py`, add fallback for missing COURSE:
```python
@classmethod
def get_all_strategies(cls):
    cls.load_graders()
    return [
        (k, v.NAME, getattr(v, 'COURSE', None) or '未分类')
        for k, v in cls._graders.items()
    ]
```

---

## Data Flow Diagrams

### Core Creation Flow (Logic Core)

```
┌─────────────────┐
│  User selects   │
│  exam + std     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Both files selected?           │──No──▶ Wait for second file
└────────┬────────────────────────┘
         │ Yes
         ▼
┌─────────────────────────────────┐
│  Call /api/ai/extract_course    │
│  (exam_file_id, std_file_id)    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Auto-fill course_name field    │
│  (user can edit)                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  User clicks "Auto-generate     │
│  Name" button                   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Call /api/ai/generate_name     │
│  (exam_file_id, std_file_id,    │
│   course_name)                  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Auto-fill task_name field      │
│  (user can edit)                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  User submits form              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Create ai_task record          │
│  with name, course_name         │
└─────────────────────────────────┘
```

---

### Task Creation Flow

```
┌─────────────────┐
│  User visits    │
│  /new_class     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  GET /api/strategies            │
│  (factory returns tuples)       │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Render dropdown with:          │
│  - Core name (from tuple[1])    │
│  - Course name (from tuple[2])  │
│  - Fallback: "未分类" if None   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  User selects core              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Auto-fill course_name field    │
│  (from tuple[2])                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  User completes form & submits  │
└─────────────────────────────────┘
```

---

## Validation Rules

### Core Name (task_name)

| Rule | Description |
|------|-------------|
| Required | Must not be empty |
| Max Length | 200 characters |
| Format | `[Year/Season]-[CourseName]-[AssignmentType]批改核心` (suggested) |
| Editable | User can override AI suggestion |

### Course Name (course_name)

| Rule | Description |
|------|-------------|
| Required | Must not be empty on submission |
| Max Length | 100 characters |
| Source | File metadata → AI extraction → Manual entry |
| Editable | User can override auto-fill |

### File Selection

| Rule | Description |
|------|-------------|
| Required | Both exam and standard must be selected |
| Format | PDF, DOC, DOCX, TXT supported |
| Validation | Files must exist in `file_assets` table |

---

## State Transitions

### AI Task Creation

```
[Draft] → [Validating] → [Generating] → [Completed]
            ↓              ↓
         [Error]        [Error]
```

**States**:
- **Draft**: User filling form, files selected
- **Validating**: Verifying file integrity
- **Generating**: AI creating grader code
- **Completed**: Core ready for use
- **Error**: Generation failed, user can retry

### Metadata Extraction

```
[Idle] → [Extracting] → [Success]
            ↓
         [Failed] → [Manual Entry]
```

---

## Indexes

No new indexes required. Existing indexes on:
- `ai_tasks.grader_id`
- `file_assets.file_hash`
- `classes.strategy`

---

## Migration Notes

**No database migration required** - this feature uses existing schema.

**Code migration required**:
1. Update `BASE_CREATOR_PROMPT` to include `COURSE` attribute instruction
2. Add fallback in `GraderFactory.get_all_strategies()`
3. Update template rendering to handle `None` values

---

## Data Quality Considerations

### Legacy Data

| Issue | Impact | Resolution |
|-------|--------|------------|
| Existing cores with `COURSE = None` | Display shows "None" | Fallback to "未分类" |
| Existing cores with generic names | Hard to identify | Bulk-edit feature (FR-013) |

### New Data

| Requirement | Enforcement |
|-------------|--------------|
| `course_name` non-NULL on creation | Form validation + prompt instruction |
| Name format consistency | AI prompt + user override allowed |
| Metadata completeness | AI analysis fallback |

---

## Glossary

| Term | Definition |
|------|------------|
| **Core** | A grading configuration (AI Task) that defines how to grade assignments |
| **Logic Core** | AI generates Python script for local execution |
| **Direct AI Core** | AI directly grades using multimodal capabilities |
| **Strategy** | Synonym for Core; used in factory and dropdowns |
| **Grader** | Python class inheriting from `BaseGrader` |
| **File Asset** | Uploaded document stored in `file_assets` table |
