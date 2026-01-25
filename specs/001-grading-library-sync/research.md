# Research: 自动评分结果同步到文���库

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Date**: 2026-01-26

## Integration Points

### 1. Batch Grading Entry Point

**File**: `blueprints/grading.py:101-108`

```python
@bp.route('/run_grading_logic/<int:class_id>', methods=['POST'])
def run_batch_grading(class_id):
    students = db.get_students_with_grades(class_id)
    db.clear_grades(class_id)
    for s in students:
        GradingService.grade_single_student(class_id, s['student_id'])
    return jsonify({"msg": "批量批改完成"})
```

**Decision**: After the `for` loop completes, insert score document generation call before `return`. This ensures:
- All grades are saved to DB before document generation
- Generation failure doesn't block the grading response (wrap in try/except)

### 2. Grade Storage

**File**: `services/grading_service.py:70-71`

```python
db.save_grade(str(student_id), class_id, result.total_score, result.get_details_json(),
              result.get_deduct_str(), status, matched_file)
```

**Data Available**:
- `student_id` - 学号
- `class_id` - 班级ID
- `result.total_score` - 总分
- `result.get_details_json()` - JSON格式的分项成绩 `[{"name": "Task1", "score": 10}, ...]`
- `result.get_deduct_str()` - 扣分详情
- `status` - PASS/FAIL

### 3. Grader Metadata

**File**: `grading_core/base.py:62-63`

```python
COURSE = "Generic Course"  # 课程名称
```

Each grader has a `COURSE` class attribute. Access via `grader.COURSE` to get course name.

## Database Schema Analysis

### grades Table (Source)

```sql
CREATE TABLE grades (
    id             INTEGER PRIMARY KEY,
    student_id     TEXT,
    class_id       INTEGER,
    total_score    REAL,
    score_details  TEXT,     -- JSON: [{"name": "...", "score": ...}, ...]
    deduct_details TEXT,
    status         TEXT,     -- PASS/FAIL
    filename       TEXT,
    UNIQUE (student_id, class_id)
);
```

### file_assets Table (Target)

```sql
CREATE TABLE file_assets (
    id             INTEGER PRIMARY KEY,
    file_hash      TEXT UNIQUE NOT NULL,  -- Use content hash or UUID
    original_name  TEXT,                  -- "2025-2026学年度第一学期-Python-软工2401班-机考分数.md"
    file_size      INTEGER,
    physical_path  TEXT,                  -- NULL (content in parsed_content)
    parsed_content TEXT,                  -- Markdown score table
    meta_info      TEXT,                  -- JSON metadata
    doc_category   TEXT DEFAULT 'exam',   -- Use 'other' for score documents
    academic_year  TEXT,
    semester       TEXT,
    course_name    TEXT,
    cohort_tag     TEXT,
    uploaded_by    INTEGER,
    created_at     TIMESTAMP
);
```

**New Field Required**: `source_class_id INTEGER` to link back to originating class for export.

### classes Table

```sql
CREATE TABLE classes (
    id             INTEGER PRIMARY KEY,
    name           TEXT,        -- 班级名称 (e.g., "软工2401班")
    course         TEXT,        -- 课程名称 (e.g., "Python程序设计")
    workspace_path TEXT,
    strategy       TEXT,        -- grader_id
    created_by     INTEGER,
    created_at     TIMESTAMP
);
```

### ai_tasks Table (Metadata Tracing)

```sql
CREATE TABLE ai_tasks (
    id            INTEGER PRIMARY KEY,
    name          TEXT,
    status        TEXT,
    grader_id     TEXT,        -- Links to grader strategy
    exam_path     TEXT,        -- Path to exam file (file_assets)
    standard_path TEXT,
    course_name   TEXT,
    max_score     INTEGER DEFAULT 100,
    ...
);
```

**Tracing Path**:
`classes.strategy` → `ai_tasks.grader_id` → `ai_tasks.exam_path` → `file_assets.meta_info`

### students Table

```sql
CREATE TABLE students (
    id         INTEGER PRIMARY KEY,
    student_id TEXT,       -- 学号
    name       TEXT,       -- 姓名
    gender     TEXT,       -- 性别 (may be NULL)
    class_id   INTEGER
);
```

## Metadata Traceability

### Source Chain

1. **Class** → `classes.strategy` (grader_id)
2. **AI Task** → `ai_tasks` WHERE `grader_id = classes.strategy`
3. **Exam File** → `file_assets` WHERE path matches `ai_tasks.exam_path`
4. **Exam Metadata** → `file_assets.meta_info` JSON contains:
   - `teacher` - 教师名称
   - `course_code` - 课程编码
   - `academic_year_semester` - 学年学期

### Query Pattern

```python
def get_exam_metadata_for_class(class_id):
    """从班级追溯到试卷元数据"""
    conn = db.get_connection()

    # 1. Get grader_id from class
    cls = conn.execute("SELECT strategy FROM classes WHERE id = ?", (class_id,)).fetchone()
    if not cls or not cls['strategy']:
        return {}

    # 2. Get ai_task by grader_id
    task = conn.execute(
        "SELECT exam_path FROM ai_tasks WHERE grader_id = ? LIMIT 1",
        (cls['strategy'],)
    ).fetchone()
    if not task or not task['exam_path']:
        return {}

    # 3. Get file_assets by path or hash
    # exam_path format: could be physical_path or original_name
    asset = conn.execute(
        "SELECT meta_info FROM file_assets WHERE physical_path = ? OR original_name LIKE ?",
        (task['exam_path'], f"%{os.path.basename(task['exam_path'])}%")
    ).fetchone()
    if not asset or not asset['meta_info']:
        return {}

    return json.loads(asset['meta_info'])
```

## Document Format

### Score Document Structure (Markdown)

```markdown
---
course_name: Python程序设计
course_code: E020001B4
class_name: 软工2401班
teacher: 张三
academic_year_semester: 2025-2026学年度第一学期
generated_at: 2026-01-26T14:30:52
source_class_id: 42
---

# 机考成绩表

| 序号 | 学号 | 姓名 | 性别 | 第一题 | 第二题 | 第三题 | 总分 |
|------|------|------|------|--------|--------|--------|------|
| 1 | 202401001 | 张三 | 男 | 20 | 25 | 30 | 75 |
| 2 | 202401002 | 李四 | 女 | 18 | 28 | 35 | 81 |
...
```

### Naming Convention

**Format**: `{academic_year_semester}-{course_name}-{class_name}-机考分数.md`

**Conflict Resolution**: Append timestamp `_YYYYMMDDHHmmss` when duplicate exists.

**Examples**:
- `2025-2026学年度第一学期-Python程序设计-软工2401班-机考分数.md`
- `2025-2026学年度第一学期-Python程序设计-软工2401班-机考分数_20260126143052.md`

## Academic Year Inference

When `academic_year_semester` is not available from exam metadata:

```python
from datetime import datetime

def infer_academic_year_semester():
    """根据当前日期推断学年学期"""
    now = datetime.now()
    year = now.year
    month = now.month

    if 9 <= month <= 12:
        # 9月-12月：当前学年第一学期
        return f"{year}-{year+1}学年度第一学期"
    elif 1 <= month <= 1:
        # 1月：上一学年第一学期（期末考试期间）
        return f"{year-1}-{year}学年度第一学期"
    else:
        # 2月-8月：上一学年第二学期
        return f"{year-1}-{year}学年度第二学期"
```

## Export Template Integration

### Current Implementation

**File**: `export_core/templates/guangwai_machinetest_score.py:67-71`

```python
# 模糊匹配班级
class_row = conn.execute("SELECT id FROM classes WHERE name LIKE ? LIMIT 1", (f"%{class_name}%",)).fetchone()
if class_row:
    class_id = class_row['id']
    db_students = db.get_students_with_grades(class_id)
```

### Enhanced Data Source Strategy

When document's `meta_info` contains `source_class_id`:

1. **Primary**: Query `grades` table directly by `class_id = source_class_id`
2. **Fallback**: Parse `parsed_content` Markdown table if class_id unavailable

```python
def get_students_data(content, meta_info, form_data):
    """获取学生成绩数据 - 增强版"""
    # 优先使用 source_class_id
    if meta_info.get('source_class_id'):
        class_id = meta_info['source_class_id']
        return db.get_students_with_grades(class_id)

    # 其次使用 class_name 模糊匹配
    class_name = form_data.get('class_name') or meta_info.get('class_name')
    if class_name:
        # ... existing fuzzy match logic
        pass

    # 最后解析 Markdown 内容
    return parse_markdown_score_table(content)
```

## Service Module Design

### Option A: Extend GradingService

Add method to `services/grading_service.py`:

```python
class GradingService:
    @staticmethod
    def generate_score_document(class_id, user_id):
        """批改完成后生成成绩文档"""
        pass
```

**Pros**: Simple, no new files
**Cons**: GradingService already handles grading logic, mixing concerns

### Option B: New ScoreDocumentService (Recommended)

Create `services/score_document_service.py`:

```python
class ScoreDocumentService:
    @staticmethod
    def generate_from_class(class_id, user_id):
        """从班级成绩生成文档"""
        pass

    @staticmethod
    def build_metadata(class_id):
        """构建元数据（含追溯逻辑）"""
        pass

    @staticmethod
    def build_markdown_content(class_id, metadata):
        """生成Markdown内容"""
        pass
```

**Pros**: Clean separation, reusable, testable
**Cons**: One more file

**Decision**: Use Option B for better modularity.

## Error Handling

### Requirements

- FR-009: Generation failure MUST NOT block grading flow
- FR-010: All existing grading behavior MUST be preserved

### Implementation

```python
# In blueprints/grading.py run_batch_grading()
try:
    ScoreDocumentService.generate_from_class(class_id, g.user['id'])
except Exception as e:
    # Log error but don't fail the request
    import logging
    logging.error(f"Score document generation failed for class {class_id}: {e}")
```

## File Hash Strategy

Since score documents are generated (not uploaded), use content-based hash:

```python
import hashlib

def generate_content_hash(content, class_id, timestamp):
    """生成内容哈希，确保唯一性"""
    unique_str = f"{class_id}:{timestamp}:{content[:100]}"
    return hashlib.sha256(unique_str.encode()).hexdigest()
```

## Validation Requirements

### Pre-Generation Checks

1. At least 1 student has successful grade (`status != 'FAIL'` or `total_score > 0`)
2. Class exists and has students

### Skip Conditions

- No students in class
- All students failed grading
- Class not found

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Naming conflict | Use timestamp suffix `_YYYYMMDDHHmmss` |
| Academic year fallback | Infer from current date |
| Document type | `doc_category = 'other'` |
| Metadata storage | JSON in `meta_info` + dedicated columns |

## Dependencies

- `database.py` - Need to add `source_class_id` migration
- `export_core/doc_config.py` - May need new schema for 'other' type (low priority)
- No new external packages required
