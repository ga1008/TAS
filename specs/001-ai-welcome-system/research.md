# Research: AI Welcome Message System

**Feature**: 001-ai-welcome-system
**Date**: 2026-01-21
**Status**: Complete

## Overview

This document summarizes research findings for the AI Welcome Message System feature. All research items have been completed and decisions documented.

## Research Topics

### 1. Existing AI Service Integration Pattern

**Question**: How does the existing codebase integrate with the AI assistant service?

**Findings**:
- AI service is hosted at `ai_assistant.py` (port 9011)
- Main app communicates via HTTP to `AI_ASSISTANT_BASE_URL` (config.py)
- Existing integration in `services/ai_service.py` using `call_ai_chat()`
- Already supports timeout handling and error fallback

**Decision**: Use existing `ai_service.call_ai_chat()` pattern

**Rationale**:
- Maintains code consistency
- Already handles timeout and error cases
- No need to duplicate HTTP client logic

**Code Reference**:
```python
# From services/ai_service.py
async def call_ai_chat(messages, system_prompt=None, model_type="standard"):
    # Existing implementation handles:
    # - HTTP calls to ai_assistant.py
    # - Timeout configuration
    # - Error handling and retries
    # - Multi-provider support
```

---

### 2. LocalStorage Key Naming Convention

**Question**: What pattern should be used for localStorage keys to track seen messages?

**Findings**:
- No existing localStorage usage in the codebase for similar tracking
- SPA navigation uses `spa_router.js` for page transitions
- Keys must be scoped to avoid conflicts with other features

**Decision**: `ai_welcome_seen_{page_context}_{message_id}`

**Rationale**:
- `ai_welcome_seen_` prefix ensures no conflicts
- `{page_context}` allows per-page tracking (dashboard, tasks, student_list)
- `{message_id}` enables tracking when content changes

**Examples**:
```javascript
localStorage.getItem('ai_welcome_seen_dashboard_12345')
localStorage.setItem('ai_welcome_seen_tasks_67890', 'true')
```

---

### 3. Streaming Animation Implementation

**Question**: How to implement the typewriter streaming effect for first-time message display?

**Findings**:
- Frontend uses Tailwind CSS with custom animations
- Existing animations defined in base.html: `fade-in`, `slide-up`, `pulse-slow`, `shake`
- Need a new typewriter/character-reveal animation

**Decision**: JavaScript character-by-character reveal with CSS transitions

**Rationale**:
- Cross-browser compatible
- No additional dependencies
- Works with SPA navigation
- Can be disabled for instant display (repeat views)

**Implementation Approach**:
```javascript
function typewriter(element, text, speed = 50) {
    let i = 0;
    element.textContent = '';
    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}
```

**CSS Enhancement**:
```css
@keyframes cursor-blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}
.typewriter-cursor::after {
    content: '|';
    animation: cursor-blink 1s infinite;
}
```

---

### 4. Time-of-Day Fallback Message Templates

**Question**: What fallback messages should be used when AI service is unavailable?

**Findings**:
- Messages should vary by time of day
- Should provide encouragement and operational guidance
- Must maintain Chinese language requirement
- Should be emotionally positive

**Decision**: Four time periods with specific templates

| Time Period | Hours | Fallback Messages |
|-------------|-------|-------------------|
| Morning | 06:00 - 11:59 | 早安！新的一天开始了，准备好处理批改任务了吗？ |
| Afternoon | 12:00 - 17:59 | 下午好！保持专注，今天还有许多任务等待完成。 |
| Evening | 18:00 - 22:59 | 晚上好！今天辛苦了，继续加油，离目标不远了。 |
| Night | 23:00 - 05:59 | 夜深了，注意休息。明天继续高效工作！ |

**Rationale**:
- Aligns with Chinese cultural norms for greetings
- Provides encouragement appropriate to time
- Simple and maintainable

---

### 5. Database Migration Approach

**Question**: How to add the new `ai_welcome_messages` table following project conventions?

**Findings**:
- Project uses `database.py` with `_migrate_table()` helper
- Automatic column addition with default values
- Thread-safe via `threading.local()`
- Row factory enables dict-style access

**Decision**: Use `_migrate_table()` pattern in `Database.__init__()`

**Implementation**:
```python
# In database.py:Database.init_db_tables()

# AI welcome messages cache table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ai_welcome_messages
    (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id          INTEGER NOT NULL,
        page_context     TEXT NOT NULL,
        message_content  TEXT NOT NULL,
        created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at       TIMESTAMP NOT NULL,
        context_snapshot TEXT
    )
''')

# Index for efficient lookups
cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_ai_welcome_user_page
    ON ai_welcome_messages(user_id, page_context)
''')

cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_ai_welcome_expires
    ON ai_welcome_messages(expires_at)
''')
```

**Rationale**:
- Follows existing pattern (e.g., `users`, `ai_providers`, `ai_models`)
- Indexes optimize common queries (by user+page, by expiration)
- `context_snapshot` stores generation context for debugging

---

## Additional Technical Decisions

### Cache Key Strategy

**Decision**: Composite key `(user_id, page_context, time_period)`

**Rationale**:
- `user_id`: Per-user personalization
- `page_context`: Different messages for different pages
- `time_period`: 4-hour blocks ensure time-sensitive greetings

**Time Periods**:
- 00:00 - 04:00 (late night)
- 04:00 - 08:00 (early morning)
- 08:00 - 12:00 (morning)
- 12:00 - 16:00 (afternoon)
- 16:00 - 20:00 (evening)
- 20:00 - 24:00 (night)

### Content Validation Rules

**Decision**: Length + character range validation

**Rules**:
```python
def validate_message(content: str) -> bool:
    # Length check
    if not (10 <= len(content) <= 200):
        return False

    # Chinese character detection (at least 50% Chinese)
    chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    if chinese_chars / len(content) < 0.5:
        return False

    # No obviously invalid patterns
    if not content.strip():
        return False

    return True
```

**Rationale**:
- Simple and fast
- Prevents obviously malformed AI output
- Doesn't over-filter valid content

---

## Open Questions Resolved

| # | Question | Resolution |
|---|----------|------------|
| 1 | How to handle AI timeout? | 5-second timeout, fallback to cached or time-based message |
| 2 | How to handle rate limiting? | Serve stale cache if available, otherwise fallback |
| 3 | Where to display on other pages? | Topbar compact slot, not on login/admin pages |
| 4 | How to trigger cache refresh? | Call `invalidate_cache()` after write operations |
| 5 | What if localStorage fails? | Treat each page load as first view (always animate) |

---

## Next Steps

With research complete, proceed to:
1. **data-model.md** - Define complete entity structure
2. **contracts/api.yaml** - Define API endpoints
3. **quickstart.md** - Development setup guide
4. **tasks.md** - Implementation task breakdown (via `/speckit.tasks`)
