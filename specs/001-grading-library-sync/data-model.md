# Data Model: 自动评分结果同步到文档库

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Date**: 2026-01-26

## Schema Changes

### file_assets Table - Add source_class_id

**Migration**: Add optional `source_class_id` column to link score documents back to their source class.

```sql
ALTER TABLE file_assets ADD COLUMN source_class_id INTEGER;
```

**Python Migration** (in `database.py` `_migrate_table`):

```python
# In init_db_tables() after file_assets creation
cursor.execute("PRAGMA table_info(file_assets)")
columns = [col[1] for col in cursor.fetchall()]
if 'source_class_id' not in columns:
    cursor.execute("ALTER TABLE file_assets ADD COLUMN source_class_id INTEGER")
```

## Entity Definitions

### ScoreDocument (Virtual Entity)

Stored in `file_assets` table with `doc_category = 'other'`.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| file_hash | TEXT | Generated | SHA256 of `{class_id}:{timestamp}:{content_prefix}` |
| original_name | TEXT | Generated | `{学年学期}-{课程}-{班级}-机考分数.md` |
| file_size | INTEGER | Computed | Length of parsed_content in bytes |
| physical_path | TEXT | NULL | No physical file, content in parsed_content |
| parsed_content | TEXT | Generated | Markdown score table |
| meta_info | TEXT | JSON | See MetaInfo structure below |
| doc_category | TEXT | 'other' | Fixed value |
| academic_year | TEXT | Extracted | From meta_info |
| semester | TEXT | Extracted | From meta_info |
| course_name | TEXT | Extracted | From class.course or grader.COURSE |
| cohort_tag | TEXT | Optional | Class identifier tag |
| source_class_id | INTEGER | Set | FK to classes.id |
| uploaded_by | INTEGER | Set | User who triggered grading |

### MetaInfo JSON Structure

```json
{
  "course_name": "Python程序设计",
  "course_code": "E020001B4",
  "class_name": "软工2401班",
  "teacher": "张三",
  "academic_year_semester": "2025-2026学年度第一学期",
  "generated_at": "2026-01-26T14:30:52",
  "source_class_id": 42,
  "student_count": 45,
  "graded_count": 43,
  "average_score": 78.5,
  "pass_rate": 0.93
}
```

### Markdown Content Structure

```markdown
# 机考成绩表

**课程**: Python程序设计 (E020001B4)
**班级**: 软工2401班
**教师**: 张三
**学期**: 2025-2026学年度第一学期
**生成时间**: 2026-01-26 14:30:52

| 序号 | 学号 | 姓名 | 性别 | 第一题 | 第二题 | 第三题 | 总分 | 状态 |
|------|------|------|------|--------|--------|--------|------|------|
| 1 | 202401001 | 张三 | 男 | 20 | 25 | 30 | 75 | PASS |
| 2 | 202401002 | 李四 | 女 | 18 | 28 | 35 | 81 | PASS |
| 3 | 202401003 | 王五 | 男 | - | - | - | 0 | 批改失败 |
...
```

## Relationships

```
classes (1) -----> (N) grades
    |                    |
    | strategy           | student_id
    v                    v
ai_tasks             students
    |
    | exam_path
    v
file_assets (exam) ---> file_assets (score_doc)
    |
    | meta_info.teacher
    | meta_info.course_code
```

## Query Patterns

### Q1: Get class metadata for document generation

```python
def get_class_metadata(class_id):
    """
    Returns: {
        'class_name': str,
        'course_name': str,
        'teacher': str | None,
        'course_code': str | None,
        'academic_year_semester': str | None
    }
    """
```

### Q2: Get all student grades with details

```python
def get_grades_for_document(class_id):
    """
    Returns: [{
        'seq': int,  # 序号
        'student_id': str,
        'name': str,
        'gender': str | None,
        'scores': [{'name': str, 'score': float}, ...],
        'total_score': float,
        'status': str  # PASS/FAIL/批改失败
    }, ...]
    """
```

### Q3: Check for existing score document

```python
def get_existing_score_document(class_id):
    """
    Returns file_asset row if exists, else None
    Used for naming conflict detection.
    """
```

### Q4: Save score document

```python
def save_score_document(class_id, user_id, original_name, content, meta_info):
    """
    Creates new file_assets record.
    Returns: asset_id
    """
```

## Data Validation Rules

### V1: Pre-generation validation

- `class_id` must exist in `classes` table
- At least one student must have a grade record (even if failed)

### V2: Content validation

- `parsed_content` must be valid Markdown
- `meta_info` must be valid JSON
- `file_hash` must be unique

### V3: Metadata completeness

- Required: `course_name`, `class_name`, `generated_at`, `source_class_id`
- Optional: `teacher`, `course_code`, `academic_year_semester`

## Index Recommendations

```sql
-- Speed up score document lookup by class
CREATE INDEX IF NOT EXISTS idx_file_assets_source_class
    ON file_assets(source_class_id)
    WHERE source_class_id IS NOT NULL;

-- Speed up document category filtering
CREATE INDEX IF NOT EXISTS idx_file_assets_category
    ON file_assets(doc_category);
```

## Backward Compatibility

- Existing `file_assets` records: `source_class_id = NULL` (unaffected)
- Existing export templates: Continue to work via `class_name` fuzzy match
- New behavior: When `source_class_id` is present, use direct lookup
