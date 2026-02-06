# Research & Technical Decisions

**Feature**: Grading Core Creation and Task Selection Improvements
**Date**: 2026-02-05
**Status**: Complete

## Research Topics

### 1. Document Metadata Structure

**Decision**: Use `file_assets.meta_info` (JSON) and `file_assets.course_name` fields

**Findings**:
- The `file_assets` table has a `meta_info` column storing JSON-formatted document metadata
- A dedicated `course_name` column exists for the course name
- When files are uploaded via the AI document parsing pipeline, metadata is extracted and stored

**Rationale**: The database schema already supports course name storage. The `meta_info` JSON field may contain additional structured data (page count, author, etc.) that can be used for context.

**Implementation Approach**:
1. First check `file_assets.course_name` (direct field)
2. If empty, parse `file_assets.meta_info` JSON for course-related fields
3. If still empty, fall back to AI content analysis

---

### 2. AI Service Capabilities

**Decision**: AI service can extract structured metadata via existing `/api/ai/chat` endpoint

**Findings**:
- AI Assistant service (`ai_assistant.py`) runs on port 9011
- Existing endpoint: `POST /api/ai/chat` accepts messages and returns structured responses
- Service already handles document parsing for grading core generation
- Can extend with new prompt templates for metadata extraction

**Rationale**: No new infrastructure needed. The AI service is designed for chat-based interaction and can be guided with specific prompts for structured extraction.

**Implementation Approach**:
1. Create new prompt templates in `config.py`:
   - `NAME_GENERATION_PROMPT` - for generating core names
   - `COURSE_EXTRACTION_PROMPT` - for extracting course names
2. Add new service functions in `services/ai_service.py`:
   - `generate_core_name(exam_file_id, standard_file_id)` → returns suggested name
   - `extract_course_name(exam_file_id, standard_file_id)` → returns course name
3. Add Flask routes in `blueprints/ai_generator.py`:
   - `POST /api/ai/generate_name`
   - `POST /api/ai/extract_course`

---

### 3. GraderFactory Implementation

**Decision**: Factory already returns COURSE; the issue is COURSE attribute is not set in generated graders

**Findings**:
- `GraderFactory.get_all_strategies()` at line 59-62 of `factory.py`:
  ```python
  return [(k, v.NAME, v.COURSE) for k, v in cls._graders.items()]
  ```
- The factory DOES return COURSE - it's the third element of the tuple
- The root cause: AI-generated graders don't have the `COURSE` class attribute set
- The `BASE_CREATOR_PROMPT` in `config.py` (line 37+) only mentions `ID` and `NAME`, not `COURSE`

**Rationale**: The factory is working correctly. The fix needs to happen in two places:
1. Update AI generation prompt to include COURSE attribute
2. Handle missing/None COURSE values in the UI with fallback labels

**Implementation Approach**:
1. **Backend Fix** (FR-009): Update `BASE_CREATOR_PROMPT` to instruct AI to set COURSE attribute
2. **UI Fix** (FR-006, FR-008): In `newClass.html`, replace `{{ course }}` with `{{ course or '未分类' }}`
3. **Factory Enhancement**: Optionally add default fallback in factory itself

---

### 4. Existing Auto-Generation Patterns

**Decision**: Follow existing prompt structure with JSON mode for structured output

**Findings**:
- Existing `BASE_CREATOR_PROMPT` uses clear instructions with code block output
- Prompt includes template showing class structure
- Uses placeholders like `{strictness_label}` for substitution
- No existing examples of metadata extraction prompts

**Rationale**: Following existing patterns ensures consistency. Add new prompts following the same structure.

**Implementation Approach**:
1. **Name Generation Prompt**:
   ```python
   NAME_GENERATION_PROMPT = """
   分析以下文档信息，生成一个批改核心名称。

   格式要求：[年份/季节]-[课程名称]-[作业类型]批改核心
   示例：2026春-数据结构-期末实验批改核心

   文档信息：
   - 试卷文件名：{exam_filename}
   - 评分标准文件名：{std_filename}
   - 课程名称：{course_name}

   只返回生成的核心名称，不要其他内容。
   """
   ```

2. **Course Extraction Prompt**:
   ```python
   COURSE_EXTRACTION_PROMPT = """
   从以下文档内容中提取课程名称。

   文档内容摘要：
   {exam_content}

   只返回课程名称，不要其他内容。
   如果无法确定课程名称，返回空字符串。
   """
   ```

---

## Best Practices Research

### 1. Form Field Ordering

**Decision**: Documents → Parameters → Instructions → Naming

**Rationale**:
- Documents are the primary input - establish context first
- Parameters (max score, strictness) depend on document context
- Instructions (extra prompts) refine the parameters
- Naming is the final step after understanding the full context
- This matches mental model: "What are we grading?" → "How do we grade it?" → "What do we call it?"

**Implementation**:
- Logic Core form: Move file uploads to top, name/course to bottom
- Direct AI form: Same reordering pattern

---

### 2. AI Prompt Engineering for Chinese Documents

**Decision**: Use explicit format instructions with examples

**Rationale**:
- Chinese course names and academic terms need clear patterns
- Providing examples (like "2026春-数据结构-期末实验") guides AI output
- Requesting "only return the result" reduces extra text

**Implementation**:
- Include Chinese examples in prompts
- Specify output format explicitly
- Use temperature ~0.3 for consistent results

---

### 3. Progressive Enhancement

**Decision**: Manual entry always available as fallback

**Rationale**:
- AI services may be temporarily unavailable
- AI may generate incorrect results
- Users should never be blocked from proceeding

**Implementation**:
- All AI features are enhancements, not requirements
- Error messages clearly indicate what failed
- Manual input fields remain enabled regardless of AI state

---

### 4. Database Query Optimization

**Decision**: Current factory approach is efficient; no changes needed

**Rationale**:
- `GraderFactory.load_graders()` uses caching with `_loaded` flag
- Graders are loaded once per request, not per database query
- Hot-reload only happens on explicit load call
- Scale (~1000 graders) is well within Python's capabilities

**Implementation**:
- No optimization needed at factory level
- UI filtering happens client-side (already implemented)

---

## Technical Decisions Summary

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| Course extraction from `meta_info` first, then AI | Faster for existing metadata; AI as fallback | AI-only (slower, more API calls) |
| Name generation via new `/api/ai/generate_name` endpoint | Follows existing service pattern; allows client-side calling | Generate on form submit (less interactive) |
| Update `BASE_CREATOR_PROMPT` to include COURSE | Fixes root cause for new cores | Database migration (doesn't fix generation) |
| Fallback label "未分类" for missing courses | User-friendly, consistent with Chinese UI | Show "None" (technical term) |
| Manual entry always available | Progressive enhancement principle | Require AI generation (blocking) |

---

## Open Questions Resolved

| Question | Answer | Source |
|----------|--------|--------|
| What is the exact structure of `meta_info` JSON? | May contain page count, author; course_name is separate field | Database schema review |
| How does factory return strategies? | Returns `[(id, NAME, COUR)]` tuple list | `factory.py` line 59-62 |
| Why are course names showing as "None"? | COURSE attribute not set in AI-generated graders | `config.py` prompt review |
| Can we batch metadata extraction? | Yes, call AI once with both files | Service design |
| What visual style to preserve? | `.glass-panel`, `bg-white/50`, hover states | `newClass.html` review |

---

## Dependencies & Integration Points

### External
- **AI Assistant Service**: `http://127.0.0.1:9011` (configurable via `AI_ASSISTANT_ENDPOINT`)

### Internal Files to Modify
1. `templates/components/form_logic.html` - Field reordering
2. `templates/components/form_direct.html` - Field reordering
3. `templates/newClass.html` - Fix course display
4. `config.py` - Add new prompt templates
5. `services/ai_service.py` - Add metadata extraction functions
6. `blueprints/ai_generator.py` - Add API routes
7. `blueprints/grading.py` - May need strategy route update
8. `grading_core/factory.py` - Add fallback for missing COURSE

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| AI service unavailable | Medium | Low | Manual entry always available |
| Metadata incomplete | High | Low | AI content analysis fallback |
| Visual regression | Low | Medium | Reuse existing CSS classes |
| Performance degradation | Low | Low | Batch calls, client-side caching |

---

## Next Steps

1. ✅ Research complete
2. → Create data-model.md
3. → Create API contracts
4. → Update agent context
