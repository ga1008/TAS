# Data Model: AI Welcome Message System

**Feature**: 001-ai-welcome-system
**Date**: 2026-01-21

## Overview

This document defines the data model for the AI Welcome Message System. The system uses SQLite for persistent storage and localStorage for client-side tracking.

## Database Schema

### Table: `ai_welcome_messages`

Cache table for AI-generated welcome messages.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier |
| `user_id` | INTEGER | NOT NULL, FOREIGN KEY → users(id) | User this message is for |
| `page_context` | TEXT | NOT NULL | Page identifier (dashboard, tasks, student_list, etc.) |
| `message_content` | TEXT | NOT NULL | The AI-generated welcome message |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When the message was generated |
| `expires_at` | TIMESTAMP | NOT NULL | When the cache expires (created_at + 4 hours) |
| `context_snapshot` | TEXT | JSON | Generation context snapshot (for debugging/regeneration) |

#### Indexes

```sql
CREATE INDEX idx_ai_welcome_user_page ON ai_welcome_messages(user_id, page_context);
CREATE INDEX idx_ai_welcome_expires ON ai_welcome_messages(expires_at);
```

#### Relationships

```
ai_welcome_messages.user_id → users.id
```

### Table: `users` (Existing)

No modifications required. Existing table referenced by foreign key.

## Python Data Models

### WelcomeMessage

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json

@dataclass
class WelcomeMessage:
    """Represents a cached AI-generated welcome message."""

    id: int
    user_id: int
    page_context: str
    message_content: str
    created_at: datetime
    expires_at: datetime
    context_snapshot: Optional[Dict[str, Any]] = None

    @property
    def is_expired(self) -> bool:
        """Check if the cached message has expired."""
        return datetime.now() > self.expires_at

    @property
    def storage_key(self) -> str:
        """Generate localStorage key for tracking seen messages."""
        return f"ai_welcome_seen_{self.page_context}_{self.id}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'page_context': self.page_context,
            'message_content': self.message_content,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'storage_key': self.storage_key
        }

    @classmethod
    def from_row(cls, row) -> 'WelcomeMessage':
        """Create from database row."""
        snapshot = None
        if row.get('context_snapshot'):
            try:
                snapshot = json.loads(row['context_snapshot'])
            except json.JSONDecodeError:
                pass

        return cls(
            id=row['id'],
            user_id=row['user_id'],
            page_context=row['page_context'],
            message_content=row['message_content'],
            created_at=datetime.fromisoformat(row['created_at']),
            expires_at=datetime.fromisoformat(row['expires_at']),
            context_snapshot=snapshot
        )
```

### MessageContext

```python
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class MessageContext:
    """Context data sent to AI for message generation."""

    # User info
    username: str

    # Time context
    current_time: str  # HH:MM format
    weekday: str  # Chinese weekday (周一, 周二, etc.)
    time_period: str  # early_morning, morning, afternoon, evening, night

    # System stats
    class_count: int
    student_count: int
    pending_task_count: int
    grader_count: int

    # Recent actions (last 3-5)
    recent_actions: List[str]

    # Page context
    page_context: str  # dashboard, tasks, student_list, ai_generator, export

    def to_prompt_dict(self) -> Dict[str, Any]:
        """Convert to dict for AI prompt formatting."""
        return asdict(self)

    @classmethod
    def from_request(cls, user_info: Dict[str, Any], stats: Dict[str, Any],
                     page_context: str, recent_actions: List[str]) -> 'MessageContext':
        """Create from request data."""
        now = datetime.now()

        # Determine time period
        hour = now.hour
        if 4 <= hour < 8:
            time_period = 'early_morning'
        elif 8 <= hour < 12:
            time_period = 'morning'
        elif 12 <= hour < 17:
            time_period = 'afternoon'
        elif 17 <= hour < 22:
            time_period = 'evening'
        else:
            time_period = 'night'

        # Chinese weekday
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

        return cls(
            username=user_info.get('username', '老师'),
            current_time=f"{hour:02d}:{now.minute:02d}",
            weekday=weekdays[now.weekday()],
            time_period=time_period,
            class_count=stats.get('class_count', 0),
            student_count=stats.get('student_count', 0),
            pending_task_count=stats.get('pending_task_count', 0),
            grader_count=stats.get('grader_count', 0),
            recent_actions=recent_actions[:5],  # Max 5 actions
            page_context=page_context
        )

    def to_snapshot(self) -> str:
        """Convert to JSON for database storage."""
        return json.dumps({
            'username': self.username,
            'time_period': self.time_period,
            'class_count': self.class_count,
            'pending_task_count': self.pending_task_count,
            'recent_actions': self.recent_actions
        })
```

### PageContext Enum

```python
from enum import Enum

class PageContext(Enum):
    """Page identifiers for welcome messages."""

    DASHBOARD = "dashboard"
    TASKS = "tasks"
    STUDENT_LIST = "student_list"
    AI_GENERATOR = "ai_generator"
    EXPORT = "export"

    @classmethod
    def from_path(cls, path: str) -> 'PageContext':
        """Determine page context from request path."""
        path_map = {
            '/': cls.DASHBOARD,
            '/tasks': cls.TASKS,
            '/student/': cls.STUDENT_LIST,
            '/ai_generator': cls.AI_GENERATOR,
            '/export': cls.EXPORT
        }
        for pattern, context in path_map.items():
            if path.startswith(pattern):
                return context
        return cls.DASHBOARD  # Default
```

## Client-Side Storage (localStorage)

### localStorage Keys

| Key Pattern | Purpose |
|-------------|---------|
| `ai_welcome_seen_{page_context}_{message_id}` | Tracks if user has seen a specific message |
| `ai_welcome_last_seen_{page_context}` | Tracks last seen message ID per page (for cleanup) |

### Example Values

```javascript
// User has seen dashboard message #123
localStorage.setItem('ai_welcome_seen_dashboard_123', 'true');

// Last seen dashboard message
localStorage.setItem('ai_welcome_last_seen_dashboard', '123');
```

## Validation Rules

### Message Content Validation

```python
import re

def validate_message_content(content: str) -> tuple[bool, Optional[str]]:
    """
    Validate AI-generated message content.

    Returns:
        (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, "Empty message"

    # Length check
    if not (10 <= len(content) <= 200):
        return False, f"Length must be 10-200 characters, got {len(content)}"

    # Chinese character proportion (at least 50%)
    chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    total_chars = len(content.strip())
    if total_chars > 0 and chinese_chars / total_chars < 0.5:
        return False, "Message must contain at least 50% Chinese characters"

    # No obviously problematic patterns
    if re.search(r'[<>{}\\]{2,}', content):  # Escaped code-like patterns
        return False, "Message contains invalid characters"

    return True, None
```

## State Transitions

### Message Lifecycle

```
[AI Generation] → [Cached & Valid] → [Expired] → [Regenerated]
                           ↓
                        [Invalidated (write op)] → [Regenerated]
```

### States

| State | Description |
|-------|-------------|
| `pending` | Message requested, not yet generated |
| `cached` | Message in database, not expired |
| `expired` | Message in database, past TTL |
| `invalidated` | Manually invalidated after write operation |

## Migration Scripts

### Initial Table Creation

```python
# In database.py:Database.init_db_tables()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ai_welcome_messages
    (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id          INTEGER NOT NULL,
        page_context     TEXT NOT NULL,
        message_content  TEXT NOT NULL,
        created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at       TIMESTAMP NOT NULL,
        context_snapshot TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_ai_welcome_user_page
    ON ai_welcome_messages(user_id, page_context)
''')

cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_ai_welcome_expires
    ON ai_welcome_messages(expires_at)
''')
```

### Cleanup Job (Optional)

For production, add periodic cleanup of expired messages:

```python
def cleanup_expired_messages():
    """Remove messages that have expired."""
    cutoff = datetime.now()
    cursor.execute('DELETE FROM ai_welcome_messages WHERE expires_at < ?', (cutoff,))
    conn.commit()
```

## Relationships Diagram

```
┌─────────────┐         ┌──────────────────────┐
│   users     │1       *│ ai_welcome_messages  │
│─────────────│─────────│──────────────────────│
│ id          │         │ id                   │
│ username    │         │ user_id              │
│ ...         │         │ page_context         │
└─────────────┘         │ message_content      │
                         │ created_at           │
                         │ expires_at           │
                         └──────────────────────┘
                                    │
                                    │ generates
                                    ↓
                         ┌──────────────────────┐
                         │   AI Assistant        │
                         │   (ai_assistant.py)  │
                         │   Port 9011           │
                         └──────────────────────┘
```
