# Quickstart: 自动评分结果同步到文档库

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Date**: 2026-01-26

## Implementation Order

### Step 1: Database Migration

**File**: `database.py`

Add `source_class_id` column to `file_assets` table.

```python
# In init_db_tables(), after file_assets table creation:
cursor.execute("PRAGMA table_info(file_assets)")
columns = [col[1] for col in cursor.fetchall()]
if 'source_class_id' not in columns:
    cursor.execute("ALTER TABLE file_assets ADD COLUMN source_class_id INTEGER")
```

---

### Step 2: Academic Year Utility

**File**: `utils/academic_year.py` (NEW)

```python
from datetime import datetime

def infer_academic_year_semester(date=None):
    """根据日期推断学年学期"""
    if date is None:
        date = datetime.now()

    year = date.year
    month = date.month

    if 9 <= month <= 12:
        return f"{year}-{year+1}学年度第一学期"
    elif month == 1:
        return f"{year-1}-{year}学年度第一学期"
    else:  # 2-8月
        return f"{year-1}-{year}学年度第二学期"
```

---

### Step 3: Score Document Service

**File**: `services/score_document_service.py` (NEW)

Core service with three methods:

1. `generate_from_class(class_id, user_id)` - Main entry point
2. `build_metadata(class_id)` - Collect metadata with tracing
3. `build_markdown_content(class_id, metadata)` - Generate Markdown

**Key Logic**:

```python
import hashlib
import json
from datetime import datetime
from extensions import db
from grading_core.factory import GraderFactory
from utils.academic_year import infer_academic_year_semester

class ScoreDocumentService:
    @staticmethod
    def generate_from_class(class_id, user_id):
        """批改完成后生成成绩文档到文档库"""
        try:
            # 1. 验证：至少有一个学生有成绩
            students = db.get_students_with_grades(class_id)
            graded = [s for s in students if s.get('total_score') is not None]
            if not graded:
                return None

            # 2. 构建元数据
            metadata = ScoreDocumentService.build_metadata(class_id)

            # 3. 生成 Markdown
            content = ScoreDocumentService.build_markdown_content(class_id, metadata)

            # 4. 生成文件名（处理冲突）
            base_name = ScoreDocumentService._generate_filename(metadata)
            final_name = ScoreDocumentService._resolve_filename_conflict(class_id, base_name)

            # 5. 生成哈希
            timestamp = datetime.now().isoformat()
            file_hash = hashlib.sha256(
                f"{class_id}:{timestamp}:{content[:100]}".encode()
            ).hexdigest()

            # 6. 保存到 file_assets
            asset_id = db.save_file_asset({
                'file_hash': file_hash,
                'original_name': final_name,
                'file_size': len(content.encode('utf-8')),
                'physical_path': None,
                'parsed_content': content,
                'meta_info': json.dumps(metadata, ensure_ascii=False),
                'doc_category': 'other',
                'course_name': metadata.get('course_name'),
                'source_class_id': class_id,
                'uploaded_by': user_id
            })

            return {'asset_id': asset_id, 'filename': final_name}

        except Exception as e:
            import logging
            logging.error(f"Score document generation failed for class {class_id}: {e}")
            return None
```

---

### Step 4: Database Helper Methods

**File**: `database.py`

Add these methods to `Database` class:

```python
def get_task_by_grader_id(self, grader_id):
    """通过 grader_id 获取 AI 任务"""
    conn = self.get_connection()
    return conn.execute(
        "SELECT * FROM ai_tasks WHERE grader_id = ? LIMIT 1",
        (grader_id,)
    ).fetchone()

def get_file_asset_by_path(self, path):
    """通过路径获取文件资产"""
    conn = self.get_connection()
    import os
    basename = os.path.basename(path)
    return conn.execute(
        "SELECT * FROM file_assets WHERE physical_path = ? OR original_name LIKE ?",
        (path, f"%{basename}%")
    ).fetchone()

def save_file_asset(self, data):
    """保存文件资产"""
    conn = self.get_connection()
    cursor = conn.execute('''
        INSERT INTO file_assets
        (file_hash, original_name, file_size, physical_path, parsed_content,
         meta_info, doc_category, course_name, source_class_id, uploaded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['file_hash'], data['original_name'], data['file_size'],
        data.get('physical_path'), data['parsed_content'], data['meta_info'],
        data['doc_category'], data.get('course_name'), data.get('source_class_id'),
        data.get('uploaded_by')
    ))
    conn.commit()
    return cursor.lastrowid

def count_score_documents_for_class(self, class_id):
    """统计班级的成绩文档数量"""
    conn = self.get_connection()
    result = conn.execute(
        "SELECT COUNT(*) as cnt FROM file_assets WHERE source_class_id = ?",
        (class_id,)
    ).fetchone()
    return result['cnt'] if result else 0
```

---

### Step 5: Integration Point

**File**: `blueprints/grading.py`

Modify `run_batch_grading()` to call document generation:

```python
@bp.route('/run_grading_logic/<int:class_id>', methods=['POST'])
def run_batch_grading(class_id):
    # 批量批改逻辑，循环调用 Service
    students = db.get_students_with_grades(class_id)
    db.clear_grades(class_id)
    for s in students:
        GradingService.grade_single_student(class_id, s['student_id'])

    # === NEW: 生成成绩文档 ===
    try:
        from services.score_document_service import ScoreDocumentService
        result = ScoreDocumentService.generate_from_class(class_id, g.user['id'])
        if result:
            print(f"[ScoreDoc] Generated: {result['filename']}")
    except Exception as e:
        import logging
        logging.error(f"[ScoreDoc] Generation failed: {e}")
    # === END NEW ===

    return jsonify({"msg": "批量批改完成"})
```

---

### Step 6: Export Template Enhancement (Optional P2)

**File**: `export_core/templates/guangwai_machinetest_score.py`

Enhance data source logic to prefer `source_class_id`:

```python
# In generate() method, replace class lookup logic:

# Priority 1: Use source_class_id from meta_info
class_id = None
if meta_info and meta_info.get('source_class_id'):
    class_id = meta_info['source_class_id']

# Priority 2: Fuzzy match by class_name
if not class_id and class_name:
    class_row = conn.execute(
        "SELECT id FROM classes WHERE name LIKE ? LIMIT 1",
        (f"%{class_name}%",)
    ).fetchone()
    if class_row:
        class_id = class_row['id']

# Fetch grades if class found
if class_id:
    db_students = db.get_students_with_grades(class_id)
    # ... process students ...
```

---

## Testing Checklist

1. [ ] Run batch grading on a class with students
2. [ ] Verify score document appears in document library
3. [ ] Check document content has correct format
4. [ ] Verify metadata fields are populated
5. [ ] Test with missing exam metadata (should use fallbacks)
6. [ ] Run grading twice, verify timestamp suffix on second document
7. [ ] Test export template with new score document

## Files Modified

| File | Change Type | Description |
|------|-------------|-------------|
| `database.py` | MODIFY | Add migration + helper methods |
| `utils/academic_year.py` | NEW | Academic year inference |
| `services/score_document_service.py` | NEW | Core service |
| `blueprints/grading.py` | MODIFY | Integration call |
| `export_core/templates/guangwai_machinetest_score.py` | MODIFY | Enhanced data source (P2) |
