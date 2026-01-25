# Internal Contracts: 自动评分结果同步到文档库

**Feature**: [spec.md](../spec.md)
**Date**: 2026-01-26

This document defines the internal Python interfaces (contracts) between components.

## ScoreDocumentService Contract

**Module**: `services/score_document_service.py`

### generate_from_class(class_id, user_id) -> dict | None

Generate a score document from completed grades for a class.

**Parameters**:
- `class_id` (int): The class ID to generate document for
- `user_id` (int): The user ID triggering the generation

**Returns**:
- `dict` on success: `{"asset_id": int, "filename": str}`
- `None` if no grades available or generation skipped

**Raises**:
- No exceptions raised (errors logged internally)

**Side Effects**:
- Creates new record in `file_assets` table
- Logs generation result

**Example**:
```python
from services.score_document_service import ScoreDocumentService

result = ScoreDocumentService.generate_from_class(class_id=42, user_id=1)
if result:
    print(f"Generated: {result['filename']} (ID: {result['asset_id']})")
```

---

### build_metadata(class_id) -> dict

Build complete metadata for a score document by tracing through related tables.

**Parameters**:
- `class_id` (int): The class ID

**Returns**:
```python
{
    "course_name": str,        # From class.course or grader.COURSE
    "course_code": str | None, # From exam file meta_info
    "class_name": str,         # From class.name
    "teacher": str | None,     # From exam file meta_info
    "academic_year_semester": str,  # From exam or inferred
    "source_class_id": int,
    "generated_at": str,       # ISO format timestamp
}
```

**Raises**:
- `ValueError` if class not found

---

### build_markdown_content(class_id, metadata) -> str

Generate Markdown content for the score document.

**Parameters**:
- `class_id` (int): The class ID
- `metadata` (dict): Metadata from `build_metadata()`

**Returns**:
- Markdown string with header section and score table

**Raises**:
- `ValueError` if no grades found

---

## Database Contract Additions

**Module**: `database.py`

### get_task_by_grader_id(grader_id) -> dict | None

Get AI task record by grader ID for metadata tracing.

**Parameters**:
- `grader_id` (str): The grader/strategy ID

**Returns**:
- `dict` with task fields or `None`

---

### get_file_asset_by_path(path) -> dict | None

Get file asset by physical path or original name.

**Parameters**:
- `path` (str): The file path to search

**Returns**:
- `dict` with file_asset fields or `None`

---

### save_file_asset(data) -> int

Save a new file asset record.

**Parameters**:
- `data` (dict): Asset data with keys matching file_assets columns

**Returns**:
- `int`: The new asset ID

---

### count_existing_score_documents(class_id) -> int

Count existing score documents for a class (for naming conflict detection).

**Parameters**:
- `class_id` (int): The class ID

**Returns**:
- `int`: Count of existing documents

---

## Academic Year Utility Contract

**Module**: `utils/academic_year.py`

### infer_academic_year_semester(date=None) -> str

Infer academic year and semester from a date.

**Parameters**:
- `date` (datetime | None): Date to infer from, defaults to now

**Returns**:
- `str`: e.g., "2025-2026学年度第一学期"

**Rules**:
- Sept-Dec: current year - next year, 第一学期
- Jan: prev year - current year, 第一学期
- Feb-Aug: prev year - current year, 第二学期

**Example**:
```python
from utils.academic_year import infer_academic_year_semester
from datetime import datetime

# October 2025 -> "2025-2026学年度第一学期"
result = infer_academic_year_semester(datetime(2025, 10, 15))

# March 2026 -> "2025-2026学年度第二学期"
result = infer_academic_year_semester(datetime(2026, 3, 1))
```

---

## Export Template Enhanced Contract

**Module**: `export_core/templates/guangwai_machinetest_score.py`

### get_students_data(content, meta_info, form_data) -> list[dict]

Enhanced method to get student data with fallback chain.

**Priority**:
1. Direct DB query via `meta_info['source_class_id']`
2. Fuzzy class name match via `form_data['class_name']`
3. Parse `content` Markdown table (fallback)

**Returns**:
```python
[
    {
        "student_id": str,
        "name": str,
        "total": float | str,
        "details": {0: score, 1: score, ...}  # Index-keyed scores
    },
    ...
]
```

---

## Integration Contract

**Caller**: `blueprints/grading.py::run_batch_grading()`

**Contract**:
```python
@bp.route('/run_grading_logic/<int:class_id>', methods=['POST'])
def run_batch_grading(class_id):
    # ... existing grading loop ...

    # NEW: Generate score document (non-blocking)
    try:
        from services.score_document_service import ScoreDocumentService
        ScoreDocumentService.generate_from_class(class_id, g.user['id'])
    except Exception as e:
        # Log but don't fail the request
        import logging
        logging.error(f"Score doc generation failed: {e}")

    return jsonify({"msg": "批量批改完成"})
```

**Guarantee**: Score document generation failure MUST NOT affect the grading response.
