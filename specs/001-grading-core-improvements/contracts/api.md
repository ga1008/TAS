# API Contracts: Grading Core Improvements

**Feature**: 001-grading-core-improvements
**Date**: 2026-02-03
**Phase**: 1 - Design & Contracts

## Overview

This document describes the API contract updates for the grading core improvements feature. Only one existing endpoint is modified.

---

## Modified Endpoints

### POST /api/create_grader_task

Create a new grader generation task with optional extra prompt.

**Request Method**: `POST`
**Content Type**: `multipart/form-data`
**Authentication**: Required (session-based)

#### Request Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `task_name` | string | Yes | Name of the grader task | Max length: 255 |
| `strictness` | string | No | Grading strictness | Values: `loose`, `standard`, `strict` (default: `standard`) |
| `extra_prompt` | string | **No (NEW)** | Extra prompt for AI generation | Max: 2000 chars (soft limit), multi-line allowed |
| `extra_desc` | string | No | Extra description | Legacy field, kept for backward compatibility |
| `max_score` | integer | No | Maximum score | Default: 100 |
| `course_name` | string | No | Course name | Optional |
| `exam_file` | file | Yes | Exam document | Formats: doc, docx, pdf, txt, md |
| `exam_file_id` | string | No | Reuse existing exam file | Alternative to exam_file |
| `standard_file` | file | Yes | Grading standard document | Formats: doc, docx, pdf, txt, md |
| `standard_file_id` | string | No | Reuse existing standard file | Alternative to standard_file |

#### Request Example

```http
POST /api/create_grader_task HTTP/1.1
Content-Type: multipart/form-data

------Boundary
Content-Disposition: form-data; name="task_name"

Python Advanced Final 2025
------Boundary
Content-Disposition: form-data; name="strictness"

standard
------Boundary
Content-Disposition: form-data; name="extra_prompt"

Please consider common typos in filenames. For example:
- test1.py might be submitted as test01.py or test_1.py
- main.py could be Main.py or MAIN.py
Try to handle these variations gracefully.
------Boundary
Content-Disposition: form-data; name="max_score"

100
------Boundary
Content-Disposition: form-data; name="course_name"

Python Advanced Programming
------Boundary
Content-Disposition: form-data; name="exam_file"; filename="exam.docx"
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document

[binary data]
------Boundary
Content-Disposition: form-data; name="standard_file"; filename="standard.pdf"
Content-Type: application/pdf

[binary data]
------Boundary--
```

#### Response

**Success (200 OK)**:

```json
{
  "msg": "任务已提交",
  "task_id": 123
}
```

**Error (400 Bad Request)**:

```json
{
  "msg": "文件缺失"
}
```

**Error (401 Unauthorized)**:

```json
{
  "msg": "Unauthorized"
}
```

#### Behavior Changes

1. **New Parameter**: `extra_prompt` field is now accepted
2. **Storage**: Stored in `ai_tasks.extra_prompt` column
3. **Usage**: Passed to AI generation service in `AiService.generate_grader_worker()`
4. **Validation**: Frontend shows warning if exceeds 2000 characters, but submission allowed
5. **Backward Compatible**: Omitting the field works as before

---

## Unchanged Endpoints

The following endpoints are NOT modified by this feature:

### GET /ai_generator

Render AI generator page.

**No changes** - Template will be updated to include extra prompt textarea, but API contract unchanged.

### GET /ai_core_list

List all graders and tasks.

**No changes** - Response structure unchanged.

### GET /grader/<grader_id>

View grader details and code.

**No changes** - Response structure unchanged.

### POST /api/create_direct_grader

Create AI direct grader.

**No changes** - Uses `extra_instruction` field (different from `extra_prompt`).

### POST /api/delete_grader

Delete a grader.

**No changes** - Request/response unchanged.

---

## New Frontend Behavior

### Form Validation (Client-Side)

The AI generator form will include client-side validation for the `extra_prompt` field:

```javascript
// Character counter with soft limit warning
const MAX_CHARS = 2000;
const WARNING_THRESHOLD = 1800;

function updateCharCounter(textarea) {
  const length = textarea.value.length;
  const counter = document.getElementById('char-counter');
  const warning = document.getElementById('char-warning');

  counter.textContent = `${length}/${MAX_CHARS}`;

  if (length > MAX_CHARS) {
    counter.classList.add('text-red-500');
    warning.textContent = '超过推荐长度，可能增加AI费用';
    warning.classList.remove('hidden');
  } else if (length > WARNING_THRESHOLD) {
    counter.classList.add('text-orange-500');
    warning.textContent = '接近推荐长度';
    warning.classList.remove('hidden');
  } else {
    counter.classList.remove('text-red-500', 'text-orange-500');
    warning.classList.add('hidden');
  }
}
```

### Form Submission (Client-Side)

```javascript
// Form submission with extra prompt
const form = document.getElementById('grader-form');
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const formData = new FormData(form);
  const extraPrompt = document.getElementById('extra_prompt').value;

  // Add extra_prompt to form data
  formData.append('extra_prompt', extraPrompt);

  // Check if exceeds soft limit
  if (extraPrompt.length > 2000) {
    const confirm = window.confirm(
      'Extra prompt exceeds 2000 characters. This may increase AI costs. Continue?'
    );
    if (!confirm) return;
  }

  // Submit to server
  const response = await fetch('/api/create_grader_task', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  if (response.ok) {
    window.location.href = '/ai_core_list';
  } else {
    alert(result.msg);
  }
});
```

---

## Backend Implementation

### Blueprint Changes

**File**: `blueprints/ai_generator.py`

**Modified Route**: `create_task()`

```python
@bp.route('/api/create_grader_task', methods=['POST'])
def create_task():
    from blueprints.notifications import NotificationService

    name = request.form.get('task_name')
    strictness = request.form.get('strictness', 'standard')
    extra_desc = request.form.get('extra_desc', '')
    extra_prompt = request.form.get('extra_prompt', '')  # NEW
    max_score = int(request.form.get('max_score', 100))

    # ... file handling ...

    # Pass extra_prompt to worker thread
    t = threading.Thread(
        target=AiService.generate_grader_worker,
        args=(
            task_id, exam_text, std_text, strictness,
            extra_desc, extra_prompt, max_score, app_config,  # Added extra_prompt
            course_name, user_id, name
        )
    )
    t.start()

    return jsonify({"msg": "任务已提交", "task_id": task_id})
```

### Service Changes

**File**: `services/ai_service.py`

**Modified Function**: `generate_grader_worker()`

```python
def generate_grader_worker(task_id, exam_text, std_text, strictness,
                          extra_desc, extra_prompt, max_score, app_config,
                          course_name, user_id, task_name):
    """
    Generate grader code using AI.

    NEW PARAM: extra_prompt - Extra guidance for logic core generation
    """
    # Build generation prompt
    prompt = build_generation_prompt(
        exam_text, std_text, strictness, extra_prompt
    )

    # Call AI
    response = asyncio.run(call_ai_platform_chat(
        system_prompt="You are an expert Python grader generator...",
        messages=[{"role": "user", "content": prompt}],
        platform_config=ai_config
    ))

    # Parse and save grader
    grader_id = save_generated_grader(response, task_name)

    # Update database
    db.update_ai_task(task_id, grader_id=grader_id, status='success')
```

---

## Error Handling

### New Error Conditions

| Error | Condition | Response | Handling |
|-------|-----------|----------|----------|
| `extra_prompt` too large | >2000 characters | Warning, allow submission | Client-side confirmation |
| File encoding fails | Base64 or upload error | Log warning, skip file | Continue with remaining files |
| File too large | >512 MB | Log warning, skip file | Continue with remaining files |
| Too many media files | >10 files | Return error | Fail grading request |
| AI model unavailable | No vision-capable model | Return error | Fail grading request |

### Error Response Format

```json
{
  "msg": "Error description",
  "error_code": "FILE_TOO_LARGE" | "AI_UNAVAILABLE" | "TOO_MANY_FILES"
}
```

---

## Testing

### Unit Tests

**File**: `tests/unit/test_ai_generator.py`

```python
def test_create_grader_with_extra_prompt():
    """Test grader creation with extra prompt"""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = test_user_id

        response = client.post('/api/create_grader_task', data={
            'task_name': 'Test Grader',
            'extra_prompt': 'Consider file name typos',
            'exam_file': (io.BytesIO(b'exam content'), 'exam.txt'),
            'standard_file': (io.BytesIO(b'standard'), 'standard.txt')
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'task_id' in data

        # Verify extra_prompt was saved
        task = db.get_ai_task_by_id(data['task_id'])
        assert task['extra_prompt'] == 'Consider file name typos'
```

### Integration Tests

```python
def test_extra_prompt_in_generation():
    """Test that extra_prompt is used in AI generation"""
    # Mock AI service to verify prompt includes extra_prompt
    with patch('services.ai_service.call_ai_platform_chat') as mock_ai:
        mock_ai.return_value = MOCK_GRADER_CODE

        create_grader_with_extra_prompt("Handle filename variations")

        # Verify AI was called with extra_prompt in the prompt
        call_args = mock_ai.call_args
        prompt = call_args[1]['messages'][0]['content']
        assert 'Handle filename variations' in prompt
```

---

## References

- `spec.md` - Functional requirements
- `data-model.md` - Database schema changes
- `research.md` - Technical research findings
- `blueprints/ai_generator.py` - Current implementation
- `services/ai_service.py` - AI service layer
