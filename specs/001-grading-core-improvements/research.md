# Research: Grading Core Improvements

**Feature**: 001-grading-core-improvements
**Date**: 2026-02-03
**Phase**: 0 - Research & Technology Decisions

## Research Summary

All unknowns from the plan have been resolved through codebase exploration and analysis of Volcengine documentation.

---

## Research Task 1: Volcengine Files API Integration

### Decision: Fix Message Structure in `direct_grader_template.py`

**Finding**: The current implementation has critical bugs in how it formats messages for Volcengine's Responses API.

**Issues Identified**:

1. **Incorrect Message Structure** (Line 148-154):
   ```python
   # Current (WRONG):
   messages = [{
       "role": "user",
       "content": user_content,  # Should be a list, not a string
       "file_ids": uploaded_file_ids
   }]
   ```

2. **Mixed Content Format**: The code tries to put text and files in separate fields, but Volcengine expects them in a single `content` array.

3. **Missing Proper Content List Structure**: Volcengine expects:
   ```python
   messages = [{
       "role": "user",
       "content": [
           {"type": "input_text", "text": "..."},
           {"type": "input_file", "file_id": "file-xxxxx"},
           {"type": "input_image", "image_url": {"url": "data:image/png;base64,..."}}
       ]
   }]
   ```

**Rationale**:
- Images use base64 encoding: `data:image/png;base64,<b64_string>`
- Videos/PDFs use Files API: file_id from `VolcFileManager.upload_file()`
- All content items go in the same `content` array
- Each content item has a `type` field indicating its format

**Alternatives Considered**:
- **Option A**: Use Files API for all media types → Rejected because images are typically small and base64 is simpler
- **Option B**: Use base64 for all files → Rejected because videos/PDFs exceed size limits and Volcengine recommends Files API for files >50 MB
- **Option C (CHOSEN)**: Hybrid approach - base64 for images, Files API for videos/PDFs → Balances simplicity and performance

**Implementation Required**:
1. Restructure message content to be a list
2. Add text content as `{"type": "input_text", "text": user_content}`
3. Add images as `{"type": "input_image", "image_url": {"url": "data:image/png;base64,..."}}`
4. Add videos/PDFs as `{"type": "input_file", "file_id": "..."}`
5. Remove the separate `file_ids` field from message structure

---

## Research Task 2: Database Migration Approach

### Decision: Use Code-Based Migration in `database.py`

**Finding**: The codebase uses a `_migrate_table()` helper method for schema migrations.

**Pattern** (from `database.py` lines 419-429):
```python
def _migrate_table(self, cursor, conn, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        conn.commit()
        print(f"[Migration] Added {column} to {table}")
```

**Usage** (from `database.py` line 393):
```python
self._migrate_table(cursor, conn, "ai_tasks", "extra_desc", "TEXT DEFAULT ''")
```

**Rationale**:
- Consistent with existing patterns in the codebase
- No separate migration files needed
- Automatic migration on app startup
- Safe (checks if column exists before adding)

**Alternatives Considered**:
- **Option A**: Manual SQL script → Rejected because codebase uses code-based migrations
- **Option B**: Alembic or Flask-Migrate → Rejected because overkill for simple column addition
- **Option C (CHOSEN)**: Use existing `_migrate_table()` pattern → Consistent with codebase conventions

**Implementation Required**:
Add this line in `database.py` after line 395:
```python
self._migrate_table(cursor, conn, "ai_tasks", "extra_prompt", "TEXT DEFAULT ''")
```

---

## Research Task 3: Base64 Encoding for Volcengine

### Decision: Use Data URL Format for Images

**Finding**: Volcengine's Responses API expects base64 images in a specific data URL format.

**Correct Format**:
```python
data_url = f"data:{mime_type};base64,{base64_string}"
# Example: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
```

**In Content Array**:
```python
{
    "type": "input_image",
    "image_url": {
        "url": "data:image/png;base64,iVBORw0KGgo..."
    }
}
```

**Rationale**:
- Matches Volcengine's documented format in ARC_doc.md
- Consistent with OpenAI's vision API format
- Works with `ai_helper.py` which detects file_ids and switches to Responses API

**Implementation Required**:
1. Keep existing base64 encoding logic in template
2. Wrap in proper content structure: `{"type": "input_image", "image_url": {"url": data_url}}`
3. Add to content array instead of separate `file_ids` field

---

## Research Task 4: Glassmorphic Design System

### Decision: Use Existing `.glass-input` Class with Tailwind Extensions

**Finding**: The codebase has a well-defined glassmorphic design system with consistent CSS classes.

**Core CSS Classes** (from `templates/base.html`):
```css
.glass-panel {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.5);
}

.glass-input {
    background: rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(10px);
}

.glass-input:focus {
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
    border-color: #818cf8;
}
```

**Existing Textarea Pattern**:
```html
<textarea name="extra_instruction"
    class="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 h-32
           focus:outline-none focus:bg-white focus:border-sky-400
           focus:ring-4 focus:ring-sky-500/10 transition-all text-sm
           resize-none shadow-inner group-hover:bg-white"
    placeholder="例如：如果学生提交的是视频，请重点关注前30秒的自我介绍..."></textarea>
```

**Rationale**:
- Consistent with existing design system
- Uses Tailwind utility classes for layout and spacing
- Glassmorphic effect via backdrop-filter
- Clear focus states for accessibility

**Alternatives Considered**:
- **Option A**: Create new `.glass-textarea` class → Rejected because existing pattern works
- **Option B (CHOSEN)**: Use existing Tailwind + CSS pattern → Consistent with codebase

**Implementation Required**:
```html
<textarea name="extra_prompt"
    class="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 h-32
           focus:outline-none focus:bg-white focus:border-sky-400
           focus:ring-4 focus:ring-sky-500/10 transition-all text-sm
           resize-none shadow-inner group-hover:bg-white glass-input"
    placeholder="例如：请考虑学生可能将文件名拼错的情况（如test1.py写成test01.py）..."></textarea>
```

---

## Decisions Summary

| Area | Decision | Rationale |
|------|----------|-----------|
| **Volcengine Integration** | Fix message structure to use content list | Matches ARC_doc.md spec |
| **Database Migration** | Use `_migrate_table()` in `database.py` | Consistent with existing patterns |
| **Base64 Encoding** | Use data URL format: `data:<mime>;base64,<data>` | Volcengine documented format |
| **Glassmorphic Design** | Use existing `.glass-input` + Tailwind utilities | Consistent with design system |

---

## Implementation Checklist

Based on research decisions:

1. [ ] Update `database.py` to add `extra_prompt` column migration
2. [ ] Update `direct_grader_template.py` to fix message structure
3. [ ] Update `ai_generator.py` blueprint to handle `extra_prompt` field
4. [ ] Update `ai_service.py` to include `extra_prompt` in AI generation
5. [ ] Update `templates/ai_generator.html` to add extra prompt textarea
6. [ ] Add file filtering logic (512 MB limit, 5/10 file limits)
7. [ ] Add validation and warning for 2000 character soft limit
8. [ ] Add character counter to textarea
9. [ ] Test with images, videos, and PDFs
10. [ ] Update `ai_helper.py` if needed for new content format

---

## References

- `ai_utils/ARC_doc.md` - Volcengine Files API documentation
- `ai_utils/volc_file_manager.py` - File upload implementation
- `ai_utils/ai_helper.py` - AI platform abstraction layer
- `database.py` - Database schema and migrations
- `templates/base.html` - CSS class definitions
- `templates/FRONTEND_GUIDE.md` - Design system guidelines
- `grading_core/direct_grader_template.py` - Direct grader template to fix
