# Data Model: Grading Core Improvements

**Feature**: 001-grading-core-improvements
**Date**: 2026-02-03
**Phase**: 1 - Design & Contracts

## Entities Overview

This feature extends the existing `ai_tasks` table with an `extra_prompt` field. No new entities are created.

---

## Entity: ai_tasks

### Existing Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique task identifier |
| `name` | TEXT | NOT NULL | Task/grader name |
| `status` | TEXT | NOT NULL | Status: pending/processing/success/failed/deleted |
| `grader_id` | TEXT | NULL | Generated grader ID (e.g., `python_final_2025_std`) |
| `log_info` | TEXT | DEFAULT '' | Processing log or error message |
| `exam_path` | TEXT | NOT NULL | File path to exam document |
| `standard_path` | TEXT | NOT NULL | File path to grading standard document |
| `strictness` | TEXT | DEFAULT 'standard' | Grading strictness: loose/standard/strict |
| `extra_desc` | TEXT | DEFAULT '' | Extra instructions for **AI direct cores** |
| `max_score` | INTEGER | DEFAULT 100 | Maximum possible score |
| `course_name` | TEXT | NULL | Course name |
| `created_by` | INTEGER | NOT NULL | User ID who created the task |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

### New Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `extra_prompt` | TEXT | NULL, DEFAULT '' | Extra prompt for **logic core generation** |

### Field Differences

**`extra_prompt` vs `extra_desc`**:
- `extra_prompt`: Used during AI generation of **logic cores** to guide file matching, edge cases, etc.
- `extra_desc`: Used in **AI direct cores** as additional grading instructions

Both serve similar purposes but at different stages:
- `extra_prompt` → **Generation** stage (AI creates Python code)
- `extra_desc` → **Execution** stage (AI grades student submissions)

---

## Relationships

### Existing Relationships (Unchanged)

```
ai_tasks (created_by) → users (id)
ai_tasks (grader_id) → grading_core/graders/*.py (file system)
classes (strategy) → ai_tasks (grader_id)
grades (class_id) → classes (id)
```

### New Relationships

None - only extending an existing entity.

---

## Validation Rules

### Extra Prompt Field

| Rule | Description | Implementation |
|------|-------------|----------------|
| **Soft Limit** | Warn if >2000 characters | Frontend JavaScript validation + visual warning |
| **Hard Limit** | No hard limit | Allow submission with warning |
| **Special Characters** | Allow all | Properly escape when passing to AI |
| **Empty Value** | Allowed | Backward compatibility - existing cores without prompts work |
| **Multi-line** | Supported | Store newlines as-is |

### File Processing Rules (New Behavior)

| Rule | Description | Implementation |
|------|-------------|----------------|
| **File Size Limit** | Skip files >512 MB | Check file size before processing |
| **Media File Limit** | Soft: 5 files, Hard: 10 files | Count and warn/fail as needed |
| **Image Format** | Use base64 encoding | `data:<mime-type>;base64,<data>` |
| **Video Format** | Use Files API | Upload to get file_id |
| **PDF Format** | Use Files API | Upload to get file_id |
| **Error Handling** | Skip failed files, log warning | Continue with remaining files |

---

## State Transitions

### ai_tasks Lifecycle (Unchanged)

```
[Create] → pending → processing → success
                              ↘ failed → [Retry] → pending
                            → deleted
```

**States**:
- `pending`: Task created, waiting for processing
- `processing`: AI is generating the grader
- `success`: Grader generated successfully
- `failed`: Generation failed (error in `log_info`)
- `deleted`: Grader moved to trash

---

## Data Flow

### Logic Core Generation with Extra Prompt

```
[User Input]
  ├── task_name
  ├── exam_file
  ├── standard_file
  ├── strictness (loose/standard/strict)
  └── extra_prompt (NEW) ← Stored in ai_tasks.extra_prompt
        ↓
[AI Service]
  ├── Reads exam + standard content
  ├── Includes extra_prompt in generation prompt
  └── Generates Python grader code
        ↓
[File System]
  └── Saves to grading_core/graders/{grader_id}.py
        ↓
[Database]
  └── Updates ai_tasks.grader_id, status='success'
```

### AI Direct Core Execution

```
[Student Submission]
  ├── Extracted to student_dir/
  ├── Scan files
  ├── Filter by type/size/limit
  └── Prepare content:
      ├── Text files → string buffer
      ├── Images → base64 encoding
      ├── Videos → Files API upload
      └── PDFs → Files API upload
        ↓
[AI Direct Grader]
  ├── Reads exam_content, standard, extra_desc
  ├── Builds message with content list
  ├── Calls Volcengine via ai_helper
  └── Parses JSON response
        ↓
[GradingResult]
  ├── total_score
  ├── sub_scores
  └── deduct_details
```

---

## Migration Script

### Database Migration (SQL)

```sql
-- Migration: Add extra_prompt column to ai_tasks
-- Date: 2026-02-03
-- Feature: 001-grading-core-improvements

-- Add column if not exists
ALTER TABLE ai_tasks ADD COLUMN extra_prompt TEXT DEFAULT '';
```

### Implementation (Python)

Location: `database.py` in `init_db_tables()` method after line 395

```python
# Add extra_prompt column for logic core generation guidance
self._migrate_table(cursor, conn, "ai_tasks", "extra_prompt", "TEXT DEFAULT ''")
```

---

## Backward Compatibility

### Existing Data

- All existing `ai_tasks` records will have `extra_prompt = ''` (empty string)
- Logic cores generated without extra prompts will continue to work
- No migration needed for existing data

### API Compatibility

- `POST /api/create_grader_task`:
  - New `extra_prompt` field is **optional**
  - Existing clients omitting the field will work unchanged

- `GET /ai_core_list`:
  - No change to response structure

- `GET /grader/<grader_id>`:
  - No change to response structure

---

## Indexes

### Existing Indexes (No Changes)

```sql
-- Existing indexes (unchanged)
CREATE INDEX IF NOT EXISTS idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX IF NOT EXISTS idx_ai_tasks_created_by ON ai_tasks(created_by);
```

### New Indexes

None needed - `extra_prompt` is not queried.

---

## File Storage

### No New File Storage

This feature does not introduce new file storage requirements. Existing file storage patterns are used:

- Exam files → `uploads/exams/`
- Standard files → `uploads/standards/`
- Generated graders → `grading_core/graders/`

---

## References

- `docs/DATABASE_SCHEMA.md` - Full database schema
- `database.py` - Database implementation and migration logic
- `spec.md` - Feature requirements
- `research.md` - Technology research findings
