# Data Model: 全局 AI 助手

**Feature**: 002-global-ai-assistant
**Date**: 2026-01-23

## Entity Relationship Diagram

```
┌─────────────────────┐       ┌─────────────────────────┐
│       users         │       │    ai_conversations     │
├─────────────────────┤       ├─────────────────────────┤
│ id (PK)             │──┬───>│ id (PK)                 │
│ username            │  │    │ user_id (FK)            │
│ ...                 │  │    │ title                   │
└─────────────────────┘  │    │ status                  │
                         │    │ created_at              │
                         │    │ last_active_at          │
                         │    └───────────┬─────────────┘
                         │                │
                         │                │ 1:N
                         │                ▼
                         │    ┌─────────────────────────┐
                         │    │      ai_messages        │
                         │    ├─────────────────────────┤
                         │    │ id (PK)                 │
                         │    │ conversation_id (FK)    │
                         │    │ role                    │
                         │    │ content                 │
                         │    │ trigger_type            │
                         │    │ metadata_json           │
                         │    │ created_at              │
                         │    └─────────────────────────┘
                         │
                         │    ┌─────────────────────────┐
                         │    │    ai_rate_limits       │
                         └───>├───────────────��─────────┤
                              │ user_id (PK, FK)        │
                              │ last_proactive_trigger  │
                              │ updated_at              │
                              └─────────────────────────┘
```

## Tables

### 1. ai_conversations (对话会话)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 会话唯一标识 |
| user_id | INTEGER | NOT NULL, FK(users.id) | 所属用户 |
| title | TEXT | DEFAULT '新对话' | 会话标题（可由 AI 自动生成） |
| status | TEXT | DEFAULT 'active' | 状态: active / archived |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| last_active_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 最后活跃时间 |

**Indexes**:
- `idx_conversation_user`: (user_id, status)
- `idx_conversation_active`: (user_id) WHERE status = 'active'

**SQL**:
```sql
CREATE TABLE IF NOT EXISTS ai_conversations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    title           TEXT DEFAULT '新对话',
    status          TEXT DEFAULT 'active',  -- active, archived
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversation_user ON ai_conversations(user_id, status);
```

### 2. ai_messages (对话消息)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 消息唯一标识 |
| conversation_id | INTEGER | NOT NULL, FK(ai_conversations.id) | 所属会话 |
| role | TEXT | NOT NULL | 角色: user / assistant / system |
| content | TEXT | NOT NULL | 消息内容 |
| trigger_type | TEXT | DEFAULT 'user_message' | 触发类型 |
| metadata_json | TEXT | NULL | 扩展元数据 (JSON) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**Trigger Types**:
- `user_message`: 用户主动发送
- `page_change`: 页面切换自动触发
- `operation_complete`: 写入操作完成触发
- `system`: 系统消息（如会话开始）

**Indexes**:
- `idx_message_conversation`: (conversation_id, created_at)

**SQL**:
```sql
CREATE TABLE IF NOT EXISTS ai_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role            TEXT NOT NULL,          -- user, assistant, system
    content         TEXT NOT NULL,
    trigger_type    TEXT DEFAULT 'user_message',  -- user_message, page_change, operation_complete, system
    metadata_json   TEXT,                   -- 扩展元数据 (page_context, operation_type 等)
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_message_conversation ON ai_messages(conversation_id, created_at);
```

### 3. ai_rate_limits (速率限制)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | INTEGER | PRIMARY KEY, FK(users.id) | 用户唯一标识 |
| last_proactive_trigger | TIMESTAMP | NOT NULL | 最后一次主动触发时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**SQL**:
```sql
CREATE TABLE IF NOT EXISTS ai_rate_limits (
    user_id                 INTEGER PRIMARY KEY,
    last_proactive_trigger  TIMESTAMP NOT NULL,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## Validation Rules

### AIConversation
- `user_id`: 必须存在于 users 表
- `status`: 只允许 'active' 或 'archived'
- `title`: 最大 100 字符

### AIMessage
- `role`: 只允许 'user', 'assistant', 'system'
- `content`: 非空，最大 5000 字符
- `trigger_type`: 只允许预定义值
- 每个会话最多保留 100 条消息（超出时自动删除最旧的）

### AIRateLimit
- `last_proactive_trigger`: 必须是有效时间戳
- 同一用户只有一条记录（使用 UPSERT）

## State Transitions

### Conversation Status
```
           create()
              │
              ▼
         ┌────────┐
         │ active │ ◄──────────┐
         └───┬────┘            │
             │                 │
         archive()         activate()
             │                 │
             ▼                 │
        ┌──────────┐           │
        │ archived │ ──────────┘
        └──────────┘
              │
          delete()
              │
              ▼
          (removed)
```

### Message Lifecycle
```
              create()
                 │
                 ▼
         ┌──────────────┐
         │   created    │
         └──────────────┘
                 │
                 │ 当会话消息数 > 100
                 ▼
         ┌──────────────┐
         │   deleted    │ (FIFO - 最旧的先删除)
         └──────────────┘
```

## Data Access Patterns

### 常用查询

1. **获取用户当前活跃会话**:
```sql
SELECT * FROM ai_conversations
WHERE user_id = ? AND status = 'active'
ORDER BY last_active_at DESC
LIMIT 1;
```

2. **获取会话消息（分页）**:
```sql
SELECT * FROM ai_messages
WHERE conversation_id = ?
ORDER BY created_at DESC
LIMIT ? OFFSET ?;
```

3. **检查速率限制**:
```sql
SELECT * FROM ai_rate_limits
WHERE user_id = ?
  AND last_proactive_trigger > datetime('now', '-1 minute');
```

4. **清理超出的消息**:
```sql
DELETE FROM ai_messages
WHERE conversation_id = ?
  AND id NOT IN (
      SELECT id FROM ai_messages
      WHERE conversation_id = ?
      ORDER BY created_at DESC
      LIMIT 100
  );
```

## Migration Strategy

使用现有的 `_migrate_table` 辅助函数添加新表：

```python
# database.py __init__ 方法中添加

# 14. AI 对话会话表 [NEW]
cursor.execute('''CREATE TABLE IF NOT EXISTS ai_conversations ...''')

# 15. AI 对话消息表 [NEW]
cursor.execute('''CREATE TABLE IF NOT EXISTS ai_messages ...''')

# 16. AI 速率限制表 [NEW]
cursor.execute('''CREATE TABLE IF NOT EXISTS ai_rate_limits ...''')

# 创建索引
cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_user ON ai_conversations(user_id, status)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_conversation ON ai_messages(conversation_id, created_at)')
```

## Existing Table: ai_welcome_messages

保留现有表用于降级场景，不做修改：

```sql
-- 已存在，无需修改
CREATE TABLE ai_welcome_messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL,
    page_context     TEXT NOT NULL,
    message_content  TEXT NOT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at       TIMESTAMP NOT NULL,
    context_snapshot TEXT
);
```

当 AI 助手对话功能不可用时，系统可降级为单向欢迎语模式，复用此表缓存。
