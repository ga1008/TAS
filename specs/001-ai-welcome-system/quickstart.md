# Quickstart: AI Welcome Message System

**Feature**: 001-ai-welcome-system
**Date**: 2026-01-21

## Prerequisites

1. **Python 3.11+** installed
2. **Node.js 18+** (for frontend testing, optional)
3. **AI Assistant Service** running on port 9011
4. **SQLite3** for database

## Development Setup

### 1. Start AI Assistant Service

The welcome system depends on the AI assistant microservice:

```bash
# Terminal 1: Start AI assistant
python ai_assistant.py

# Service will be available at http://127.0.0.1:9011
```

### 2. Start Main Application

```bash
# Terminal 2: Start Flask app
python app.py

# Application available at http://127.0.0.1:5010
```

### 3. Verify Database Migration

On first run, the `ai_welcome_messages` table will be created automatically:

```python
from database import Database
db = Database()
# Table created automatically in init_db_tables()
```

Verify with:

```bash
sqlite3 data/grading_system_v2.db
.tables
# Should include: ai_welcome_messages

.schema ai_welcome_messages
```

## Development Workflow

### Backend Development

#### 1. Create AI Prompts Module

```bash
# Create new file
touch services/ai_prompts.py
```

```python
# services/ai_prompts.py
WELCOME_PROMPT_TEMPLATE = """
你是一个智能教学助手的欢迎语生成器。根据用户信息生成个性化欢迎语。

用户信息：
- 用户名: {username}
- 当前时间: {current_time}
- 星期: {weekday}
...
"""

def get_fallback_message(time_period: str) -> str:
    """Return time-based fallback message."""
    fallbacks = {
        'morning': '早安！新的一天开始了，准备好处理批改任务了吗？',
        'afternoon': '下午好！保持专注，今天还有许多任务等待完成。',
        ...
    }
    return fallbacks.get(time_period, fallbacks['morning'])
```

#### 2. Create AI Content Service

```bash
touch services/ai_content_service.py
```

```python
# services/ai_content_service.py
from services.ai_service import call_ai_chat
from services.ai_prompts import WELCOME_PROMPT_TEMPLATE
import json

async def generate_welcome_message(user_id: int, page_context: str, stats: dict):
    """Generate or fetch cached welcome message."""
    # Check cache first
    cached = get_cached_message(user_id, page_context)
    if cached and not cached.is_expired:
        return cached, 'cached'

    # Generate new message
    context = MessageContext.from_request(...)
    prompt = WELCOME_PROMPT_TEMPLATE.format(**context.to_prompt_dict())

    messages = [{"role": "user", "content": prompt}]
    response = await call_ai_chat(messages, model_type="standard")

    # Validate and cache
    if validate_message_content(response):
        save_to_cache(user_id, page_context, response, context)
        return response, 'generated'
    else:
        return get_fallback_message(context.time_period), 'fallback'
```

#### 3. Create Blueprint

```bash
touch blueprints/ai_welcome.py
```

```python
# blueprints/ai_welcome.py
from flask import Blueprint, jsonify, request, session
from services.ai_content_service import generate_welcome_message

bp = Blueprint('ai_welcome', __name__)

@bp.route('/api/welcome/messages', methods=['GET'])
def get_welcome():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in'}), 401

    user_id = session['user_id']
    page_context = request.args.get('page_context', 'dashboard')

    message, status = await generate_welcome_message(user_id, page_context, {})
    return jsonify({'status': status, 'data': message.to_dict()})
```

#### 4. Register Blueprint in `app.py`

```python
# app.py
from blueprints.ai_welcome import bp as ai_welcome_bp

app.register_blueprint(ai_welcome_bp)
```

### Frontend Development

#### 1. Create Welcome Component

```bash
# Create component directory
mkdir -p templates/components
touch templates/components/ai_welcome_message.html
```

```html
<!-- templates/components/ai_welcome_message.html -->
<div id="ai-welcome-container" class="glass-panel p-6 rounded-3xl relative overflow-hidden transition-all duration-300"
     data-page-context="{{ page_context or 'dashboard' }}">
    <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-indigo-100 to-blue-50 rounded-full -mr-16 -mt-16 opacity-50"></div>

    <div class="relative z-10">
        <div id="welcome-content">
            <p class="text-slate-500 font-medium">加载中...</p>
        </div>
    </div>
</div>
```

#### 2. Create Streaming Animation Script

```bash
mkdir -p static/js
touch static/js/ai-welcome.js
```

```javascript
// static/js/ai-welcome.js

async function loadWelcomeMessage(pageContext = 'dashboard') {
    const container = document.getElementById('ai-welcome-container');
    const contentEl = document.getElementById('welcome-content');

    try {
        const response = await fetch(`/api/welcome/messages?page_context=${pageContext}`);
        const data = await response.json();

        if (data.status === 'success' || data.status === 'cached' || data.status === 'generated') {
            const msg = data.data;
            const storageKey = msg.storage_key;
            const hasSeen = localStorage.getItem(storageKey) === 'true';

            if (hasSeen) {
                // Instant display for repeat views
                contentEl.innerHTML = `<p class="text-slate-700 font-medium">${msg.message_content}</p>`;
            } else {
                // Streaming animation for first view
                typewriter(contentEl, msg.message_content, () => {
                    localStorage.setItem(storageKey, 'true');
                });
            }
        }
    } catch (error) {
        console.error('Failed to load welcome message:', error);
        showFallbackMessage();
    }
}

function typewriter(element, text, callback) {
    let i = 0;
    element.innerHTML = '';

    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, 50); // 50ms per character
        } else if (callback) {
            callback();
        }
    }
    type();
}

// Auto-load on page ready
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('ai-welcome-container');
    if (container) {
        const pageContext = container.dataset.pageContext || 'dashboard';
        loadWelcomeMessage(pageContext);
    }
});
```

#### 3. Integrate into Dashboard

```html
<!-- templates/dashboard.html -->
<!-- Replace the static welcome message (around line 68) -->
<div class="glass-panel p-8 rounded-3xl relative overflow-hidden group border border-white/60 shadow-xl">
    {% include 'components/ai_welcome_message.html' %}
</div>

<!-- Add script at bottom -->
<script src="{{ url_for('static', filename='js/ai-welcome.js') }}"></script>
```

## Testing

### Unit Tests

```bash
# Run tests
pytest tests/ai_welcome/ -v

# With coverage
pytest tests/ai_welcome/ --cov=services.ai_content_service --cov-report=html
```

### Manual Testing Checklist

- [ ] **First Visit**: Clear localStorage, refresh page → should see streaming animation
- [ ] **Repeat Visit**: Refresh page → should see instant display
- [ ] **Time of Day**: Check at different times → verify appropriate fallbacks
- [ ] **AI Service Down**: Stop ai_assistant.py → should see fallback message
- [ ] **Cache Expiration**: Wait 4 hours or modify expires_at → should regenerate
- [ ] **Cross-Page**: Navigate to tasks, student list → verify different messages

### Test API Endpoints

```bash
# Get welcome message (requires active session)
curl -X GET "http://localhost:5010/api/welcome/messages?page_context=dashboard" \
  -H "Cookie: session=your_session_cookie"

# Refresh message
curl -X POST "http://localhost:5010/api/welcome/messages/refresh?page_context=dashboard" \
  -H "Cookie: session=your_session_cookie"

# Get fallback (no auth required)
curl -X GET "http://localhost:5010/api/welcome/fallback?time_of_day=morning"
```

## Debugging

### Enable Logging

```python
# In ai_content_service.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def generate_welcome_message(...):
    logger.debug(f"Generating message for user {user_id}, page {page_context}")
    ...
```

### Check Cache State

```bash
sqlite3 data/grading_system_v2.db

# View all messages
SELECT * FROM ai_welcome_messages ORDER BY created_at DESC;

# View expired messages
SELECT * FROM ai_welcome_messages WHERE expires_at < datetime('now');

# View messages for a specific user
SELECT * FROM ai_welcome_messages WHERE user_id = 1;
```

### Clear localStorage (Browser Console)

```javascript
// Clear all welcome tracking
Object.keys(localStorage)
  .filter(k => k.startsWith('ai_welcome_'))
  .forEach(k => localStorage.removeItem(k));
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Messages not loading | Check AI assistant is running on port 9011 |
| Streaming animation not working | Check browser console for JS errors |
| Cache not expiring | Verify expires_at calculation, check system time |
| Fallback always showing | Check AI service logs, verify prompt template |
| Empty messages | Check validate_message_content() function |

## Deployment

1. **Database Migration**: Automatic on first run
2. **Config Changes**: Add TTL config to `config.py` if needed
3. **Frontend Assets**: Commit `ai-welcome.js` to `static/js/`
4. **Templates**: Commit component HTML to `templates/components/`

## Rollback

If issues arise, rollback by:

1. Remove blueprint registration from `app.py`
2. Revert dashboard.html to static message
3. Table will remain but won't be used (harmless)

To clean up completely:

```sql
DROP TABLE IF EXISTS ai_welcome_messages;
```
