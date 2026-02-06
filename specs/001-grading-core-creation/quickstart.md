# Quickstart Guide: Grading Core Creation Improvements

**Feature**: Grading Core Creation and Task Selection Improvements
**Branch**: `001-grading-core-creation`
**Date**: 2026-02-05

## Prerequisites

- Python 3.8+
- Flask development environment
- AI Assistant service running on port 9011
- Access to the codebase at `C:\Users\AngelWei\Nutstore\1\Projects\autoCorrecting`

---

## Local Development Setup

### 1. Start the AI Assistant Service

```bash
# Terminal 1
cd C:\Users\AngelWei\Nutstore\1\Projects\autoCorrecting
python ai_assistant.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9011
```

### 2. Start the Flask Application

```bash
# Terminal 2
cd C:\Users\AngelWei\Nutstore\1\Projects\autoCorrecting
python app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5010
 * Running on http://192.168.x.x:5010
```

### 3. Access the Application

Open browser and navigate to:
- Main application: http://127.0.0.1:5010
- AI Generator: http://127.0.0.1:5010/ai_generator
- New Task: http://127.0.0.1:5010/new_class

---

## Feature Testing Checklist

### User Story 1: Reorganized Core Creation UI

**Logic Core Form** (`/ai_generator` - 默认推荐 tab)

- [ ] Upload exam document appears at the top
- [ ] Upload grading criteria appears second
- [ ] Max score input appears third
- [ ] Strictness selection appears fourth
- [ ] Extra generation prompt appears fifth
- [ ] Core name input appears sixth (with auto-generate button)
- [ ] Course name input appears last (with auto-fill)
- [ ] Visual styling (glass-panel, hover states) is preserved
- [ ] Form submission works correctly

**Direct AI Core Form** (`/ai_generator` - Direct AI 多模态 tab)

- [ ] Same field order as Logic Core form
- [ ] File upload areas at the top
- [ ] Extra instruction field in the middle
- [ ] Core name and course name at the bottom
- [ ] Visual styling consistent with Logic Core

---

### User Story 2: AI Auto-Generation of Core Names

- [ ] "Auto-generate Name" button appears next to core name input
- [ ] Clicking button shows loading state
- [ ] Generated name follows format: `[Year/Season]-[CourseName]-[AssignmentType]批改核心`
- [ ] User can manually edit the generated name
- [ ] If AI fails, error message appears but form can still be submitted
- [ ] Request is logged with timestamp and outcome

**Test Cases**:

1. **Well-named documents**
   - Upload: `2026春_数据结构_期末实验.pdf`
   - Expected: `2026春-数据结构-期末实验批改核心`

2. **Poorly named documents**
   - Upload: `exam.pdf` + `rubric.docx`
   - Expected: AI extracts content to generate name

3. **AI service unavailable**
   - Stop ai_assistant.py
   - Click "Auto-generate Name"
   - Expected: Error message, manual entry allowed

---

### User Story 3: Fixed Core Selection in Task Creation

**Task Creation Page** (`/new_class`)

- [ ] Core dropdown shows actual core names (not "None", not "Generic Course")
- [ ] Each dropdown option shows: core icon + name
- [ ] Cores with missing course names show "未分类" instead of "None"
- [ ] Selecting a core auto-fills the course name field
- [ ] Search box filters cores by name and course
- [ ] All existing cores are displayed correctly

**Test Cases**:

1. **New core with course name**
   - Create core with course: "数据结构与算法"
   - Go to /new_class
   - Expected: Core appears with correct course name

2. **Legacy core without course name**
   - Core created before this feature
   - Expected: Shows "未分类" as course name

3. **Search functionality**
   - Type in search box
   - Expected: List filters based on core name and course name

---

### User Story 4: Unified Naming Convention

- [ ] Both Logic Cores and Direct AI Cores display consistently
- [ ] All new cores have non-NULL `name` and `course_name`
- [ ] Dropdown sorting is consistent

---

## API Endpoint Testing

### Generate Core Name

```bash
curl -X POST http://127.0.0.1:5010/api/ai/generate_name \
  -H "Content-Type: application/json" \
  -d '{
    "exam_file_id": "abc123",
    "standard_file_id": "def456",
    "course_name": "数据结构与算法"
  }'
```

Expected response:
```json
{
  "status": "success",
  "name": "2026春-数据结构-期末实验批改核心",
  "confidence": 0.95
}
```

### Extract Course Name

```bash
curl -X POST http://127.0.0.1:5010/api/ai/extract_course \
  -H "Content-Type: application/json" \
  -d '{
    "exam_file_id": "abc123",
    "standard_file_id": "def456"
  }'
```

Expected response:
```json
{
  "status": "success",
  "course_name": "数据结构与算法",
  "source": "metadata"
}
```

### Get Strategies

```bash
curl http://127.0.0.1:5010/api/strategies
```

Expected response:
```json
[
  ["linux_final_2026_std", "Linux期末批改核心", "Linux系统编程"],
  ["java_experiment_01", "Java实验一", "Java程序设计"],
  ["direct_9fa38898", "视频作业批改核心", "未分类"]
]
```

---

## File Modifications Summary

### Templates

| File | Changes |
|------|---------|
| `templates/components/form_logic.html` | Field reordering + auto-generate button + auto-fill |
| `templates/components/form_direct.html` | Field reordering + auto-generate button + auto-fill |
| `templates/newClass.html` | Fix course display with fallback |
| `templates/ai_generator.html` | May need JavaScript updates |

### Backend

| File | Changes |
|------|---------|
| `config.py` | Add `NAME_GENERATION_PROMPT`, `COURSE_EXTRACTION_PROMPT` |
| `services/ai_service.py` | Add `generate_core_name()`, `extract_course_name()` |
| `blueprints/ai_generator.py` | Add `/api/ai/generate_name`, `/api/ai/extract_course` routes |
| `blueprints/grading.py` | May update strategy passing |
| `grading_core/factory.py` | Add fallback for missing COURSE |

---

## Debugging Tips

### AI Service Not Responding

1. Check if `ai_assistant.py` is running:
   ```bash
   curl http://127.0.0.1:9011/health
   ```

2. Check Flask logs for connection errors

3. Verify `AI_ASSISTANT_BASE_URL` in `config.py`

### Course Name Shows "None"

1. Check database for core's COURSE attribute:
   ```sql
   SELECT id, name, course_name FROM ai_tasks;
   ```

2. For Python graders, check if COURSE class attribute is set:
   ```python
   # grading_core/graders/your_grader.py
   class YourGrader(BaseGrader):
       ID = "your_grader"
       NAME = "Your Grader"
       COURSE = "Your Course Name"  # Must be set
   ```

3. Check factory output:
   ```python
   from grading_core.factory import GraderFactory
   print(GraderFactory.get_all_strategies())
   ```

### Visual Styles Not Preserved

1. Verify Tailwind classes match existing patterns
2. Check that `.glass-panel` class is applied
3. Ensure input fields use `bg-white/50` or similar
4. Verify hover states have proper transitions

---

## Regression Testing

Before marking the feature complete, verify:

- [ ] Existing grading cores still work
- [ ] File upload via modal still works
- [ ] Regenerating cores from existing tasks works
- [ ] All strictness levels function correctly
- [ ] Max score configuration is preserved
- [ ] Extra prompts are properly passed to AI
- [ ] Student list selection in task creation works
- [ ] Grade export functionality is unaffected

---

## Success Criteria Verification

| Criterion | How to Verify |
|-----------|---------------|
| SC-001: Fields in correct order | Visual inspection of both forms |
| SC-002: 90% name generation success | Test with 10 documents, count successes |
| SC-003: 80% course auto-fill success | Test with 10 documents, verify accuracy |
| SC-004: No "None" in dropdown | Inspect /new_class dropdown |
| SC-005: Page load <2 seconds | Browser network timing |
| SC-006: Zero regression | Run existing feature tests |
| SC-007: Auto-fill <3 seconds | Measure API response time |

---

## Next Steps

After implementation:

1. Run the testing checklist above
2. Fix any issues found
3. Update documentation if needed
4. Create pull request to `master` branch
5. Deploy to staging for user acceptance testing

---

## Questions or Issues?

- Constitution compliance: See [plan.md](./plan.md) Constitution Check section
- Data model details: See [data-model.md](./data-model.md)
- API contracts: See [contracts/api.yaml](./contracts/api.yaml)
- Research findings: See [research.md](./research.md)
