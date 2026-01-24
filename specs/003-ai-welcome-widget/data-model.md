# Data Model: AI 欢迎语功能改进

**Date**: 2026-01-24
**Feature**: 003-ai-welcome-widget

## 概述

本功能使用现有数据库表结构，无需新建表。以下是涉及的实体及其关系。

## 实体定义

### 1. WelcomeMessage (ai_welcome_messages 表)

存储 AI 生成的欢迎语消息。

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|-----|
| id | INTEGER | PRIMARY KEY | 自增主键 |
| user_id | INTEGER | NOT NULL, FK → users.id | 用户ID |
| page_context | TEXT | NOT NULL | 页面上下文 (dashboard, tasks, ai_generator, student_list, export) |
| message_content | TEXT | NOT NULL | AI 生成的欢迎语文本 (≤40字) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| expires_at | TIMESTAMP | NOT NULL | 缓存过期时间 |
| context_snapshot | TEXT | NULLABLE | 生成时的上下文快照 (JSON) |

**索引**:
- `idx_ai_welcome_user_page(user_id, page_context)` - 加速用户+页面查询
- `idx_ai_welcome_expires(expires_at)` - 加速过期清理

**生命周期**:
- 创建：AI 生成成功时
- 过期：TTL 到期（默认 30 分钟）或 30 天后自动清理
- 删除：用户删除或系统清理

---

### 2. Conversation (ai_conversations 表)

存储用户与 AI 助手的对话会话。

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|-----|
| id | INTEGER | PRIMARY KEY | 自增主键 |
| user_id | INTEGER | NOT NULL, FK → users.id | 用户ID |
| title | TEXT | DEFAULT '新对话' | 会话标题 |
| status | TEXT | DEFAULT 'active' | 状态 (active, archived) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| last_active_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 最后活跃时间 |

**索引**:
- `idx_conversation_user(user_id, status)` - 加速活跃会话查询

**生命周期**:
- 创建：用户首次发送消息时
- 归档：用户主动归档或长时间不活跃

---

### 3. Message (ai_messages 表)

存储对话中的每条消息。

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|-----|
| id | INTEGER | PRIMARY KEY | 自增主键 |
| conversation_id | INTEGER | NOT NULL, FK → ai_conversations.id | 会话ID |
| role | TEXT | NOT NULL | 角色 (user, assistant, system) |
| content | TEXT | NOT NULL | 消息内容 |
| trigger_type | TEXT | DEFAULT 'user_message' | 触发类型 (user_message, page_change, operation_complete, system) |
| metadata_json | TEXT | NULLABLE | 扩展元数据 (JSON) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- `idx_message_conversation(conversation_id, created_at)` - 加速历史消息查询

---

### 4. RateLimit (ai_rate_limits 表)

控制主动触发的频率限制。

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|-----|
| user_id | INTEGER | PRIMARY KEY, FK → users.id | 用户ID |
| last_proactive_trigger | TIMESTAMP | NOT NULL | 上次主动触发时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**业务规则**:
- 定时触发冷却：60 秒
- 操作触发冷却：10 秒

---

## 前端数据模型

### sessionStorage 结构

```typescript
interface ChatHistory {
  messages: ChatMessage[];
  lastUpdated: string; // ISO timestamp
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string; // ISO timestamp
}
```

**存储键**: `ai_chat_history`
**容量限制**: 最多保留最近 50 条消息

---

## 实体关系图

```
┌─────────────┐       ┌──────────────────┐
│   users     │──1:N──│ ai_welcome_msgs  │
└─────────────┘       └──────────────────┘
       │
       │ 1:N
       ▼
┌─────────────────┐       ┌─────────────┐
│ ai_conversations│──1:N──│ ai_messages │
└─────────────────┘       └─────────────┘
       │
       │ 1:1
       ▼
┌─────────────────┐
│ ai_rate_limits  │
└─────────────────┘
```

---

## 数据验证规则

### WelcomeMessage 验证

```python
def validate_message_content(content: str) -> Tuple[bool, Optional[str]]:
    # 1. 非空检查
    if not content or not content.strip():
        return False, "消息为空"

    # 2. 长度检查 (10-200 字符，但 UI 建议 ≤40)
    if not (10 <= len(content) <= 200):
        return False, f"长度应为 10-200 字符"

    # 3. 中文字符比例 ≥ 50%
    chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    if chinese_chars / len(content) < 0.5:
        return False, "中文字符不足 50%"

    # 4. 无效模式检查
    if content.startswith('```') or content.endswith('```'):
        return False, "格式无效"

    return True, None
```

---

## 状态转换

### 触发请求状态机

```
[空闲] ──触发──▶ [检查冷却] ──通过──▶ [调用AI] ──成功──▶ [显示气泡]
                    │                    │
                    ▼                    ▼
               [静默跳过]           [显示回退消息]
```

### 聊天窗口状态机

```
[关闭] ──点击按钮──▶ [展开动画] ──完成──▶ [打开]
                                          │
[关闭] ◀──收起动画──◀───点击关闭───────────┘
```
