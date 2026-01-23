# API Contracts: AI Assistant

**Feature**: 002-global-ai-assistant
**Base Path**: `/api/assistant`
**Version**: 1.0

## Endpoints Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | /conversations | 创建新对话会话 |
| GET | /conversations/active | 获取当前活跃会话 |
| GET | /conversations/{id}/messages | 获取会话消息历史 |
| POST | /conversations/{id}/messages | 发送用户消息 |
| POST | /conversations/{id}/archive | 归档会话 |
| POST | /trigger/page-change | 页面切换触发 |
| POST | /trigger/operation | 操作完成触发 |
| GET | /poll | 轮询新消息 |

---

## 1. Create Conversation

**POST** `/api/assistant/conversations`

创建新的对话会话。

### Request
```json
{
    "title": "新对话"  // 可选，默认 "新对话"
}
```

### Response (201 Created)
```json
{
    "status": "success",
    "data": {
        "id": 123,
        "user_id": 1,
        "title": "新对话",
        "status": "active",
        "created_at": "2026-01-23T10:30:00",
        "last_active_at": "2026-01-23T10:30:00"
    }
}
```

### Error Responses
- `401 Unauthorized`: 未登录
- `500 Internal Server Error`: 服务器错误

---

## 2. Get Active Conversation

**GET** `/api/assistant/conversations/active`

获取当前用户的活跃会话，如果没有则自动创建一个。

### Request
无参数

### Response (200 OK)
```json
{
    "status": "success",
    "data": {
        "id": 123,
        "user_id": 1,
        "title": "新对话",
        "status": "active",
        "created_at": "2026-01-23T10:30:00",
        "last_active_at": "2026-01-23T10:30:00",
        "message_count": 15
    }
}
```

---

## 3. Get Conversation Messages

**GET** `/api/assistant/conversations/{conversation_id}/messages`

获取指定会话的消息历史（支持分页）。

### Request Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | int | No | 20 | 每页消息数 (1-100) |
| offset | int | No | 0 | 偏移量 |
| order | string | No | "desc" | 排序: "asc" / "desc" |

### Response (200 OK)
```json
{
    "status": "success",
    "data": {
        "messages": [
            {
                "id": 456,
                "role": "assistant",
                "content": "早安，张老师！有什么我可以帮您的吗？",
                "trigger_type": "page_change",
                "created_at": "2026-01-23T10:30:15",
                "metadata": {
                    "page_context": "dashboard"
                }
            },
            {
                "id": 457,
                "role": "user",
                "content": "我想创建一个新的批改任务",
                "trigger_type": "user_message",
                "created_at": "2026-01-23T10:31:00",
                "metadata": null
            }
        ],
        "pagination": {
            "total": 15,
            "limit": 20,
            "offset": 0,
            "has_more": false
        }
    }
}
```

### Error Responses
- `401 Unauthorized`: 未登录
- `403 Forbidden`: 无权访问该会话
- `404 Not Found`: 会话不存在

---

## 4. Send Message

**POST** `/api/assistant/conversations/{conversation_id}/messages`

发送用户消息并获取 AI 回复。

### Request
```json
{
    "content": "我想创建一个新的批改任务",
    "page_context": "dashboard"  // 可选，当前页面上下文
}
```

### Response (200 OK)
```json
{
    "status": "success",
    "data": {
        "user_message": {
            "id": 457,
            "role": "user",
            "content": "我想创建一个新的批改任务",
            "trigger_type": "user_message",
            "created_at": "2026-01-23T10:31:00"
        },
        "assistant_message": {
            "id": 458,
            "role": "assistant",
            "content": "好的！创建批改任务很简单。请先进入"AI 生成"页面，然后按照以下步骤操作：\n1. 上传试卷文档（PDF 或图片）\n2. 上传评分标准\n3. 点击"生成批改核心"\n\n系统会自动分析您的试卷并生成批改脚本。需要我帮您导航到该页面吗？",
            "trigger_type": "user_message",
            "created_at": "2026-01-23T10:31:05"
        }
    }
}
```

### Error Responses
- `400 Bad Request`: 消息内容为空或过长
- `401 Unauthorized`: 未登录
- `403 Forbidden`: 无权访问该会话
- `503 Service Unavailable`: AI 服务不可用

---

## 5. Archive Conversation

**POST** `/api/assistant/conversations/{conversation_id}/archive`

归档会话（创建"新对话"时自动归档当前会话）。

### Request
无参数

### Response (200 OK)
```json
{
    "status": "success",
    "message": "会话已归档"
}
```

---

## 6. Page Change Trigger

**POST** `/api/assistant/trigger/page-change`

页面切换时触发 AI 主动问候。受 1 分钟间隔限制。

### Request
```json
{
    "page_context": "ai_generator",
    "page_url": "/ai_generator"  // 可选，用于日志
}
```

### Response (200 OK) - 允许触发
```json
{
    "status": "success",
    "data": {
        "triggered": true,
        "message": {
            "id": 459,
            "role": "assistant",
            "content": "欢迎来到 AI 生成页面！这里是创建批改核心的地方。您可以上传试卷和评分标准，系统会自动生成批改脚本。需要帮助吗？",
            "trigger_type": "page_change",
            "created_at": "2026-01-23T10:35:00",
            "metadata": {
                "page_context": "ai_generator"
            }
        }
    }
}
```

### Response (200 OK) - 被限制
```json
{
    "status": "success",
    "data": {
        "triggered": false,
        "reason": "rate_limited",
        "retry_after": 45  // 剩余冷却秒数
    }
}
```

---

## 7. Operation Complete Trigger

**POST** `/api/assistant/trigger/operation`

写入操作完成时触发 AI 反馈。受 1 分钟间隔限制。

### Request
```json
{
    "operation_type": "generate_grader",  // 操作类型
    "operation_result": "success",        // success / error
    "operation_details": {                // 操作详情（可选）
        "grader_name": "计算机基础期末考试",
        "question_count": 5
    }
}
```

### Supported Operation Types
- `generate_grader`: 生成批改核心
- `parse_document`: 解析文档
- `export_grades`: 导出成绩
- `import_students`: 导入学生名单
- `create_class`: 创建班级

### Response (200 OK)
```json
{
    "status": "success",
    "data": {
        "triggered": true,
        "message": {
            "id": 460,
            "role": "assistant",
            "content": "太棒了！《计算机基础期末考试》批改核心已成功生成，包含 5 道题目的评分逻辑。现在您可以创建班级并上传学生作业了。要我帮您导航到班级管理页面吗？",
            "trigger_type": "operation_complete",
            "created_at": "2026-01-23T10:40:00"
        }
    }
}
```

---

## 8. Poll for New Messages

**GET** `/api/assistant/poll`

轮询新消息（用于多标签页同步）。

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| conversation_id | int | Yes | 当前会话 ID |
| last_message_id | int | Yes | 已知的最后消息 ID |

### Response (200 OK) - 有新消息
```json
{
    "status": "success",
    "data": {
        "has_new": true,
        "messages": [
            {
                "id": 461,
                "role": "assistant",
                "content": "...",
                "trigger_type": "page_change",
                "created_at": "2026-01-23T10:42:00"
            }
        ]
    }
}
```

### Response (200 OK) - 无新消息
```json
{
    "status": "success",
    "data": {
        "has_new": false,
        "messages": []
    }
}
```

---

## Common Error Response Format

```json
{
    "status": "error",
    "error": {
        "code": "RATE_LIMITED",
        "message": "请求过于频繁，请稍后再试",
        "details": {
            "retry_after": 45
        }
    }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | 未登录 |
| FORBIDDEN | 403 | 无权访问 |
| NOT_FOUND | 404 | 资源不存在 |
| INVALID_REQUEST | 400 | 请求参数无效 |
| RATE_LIMITED | 429 | 请求过于频繁 |
| AI_UNAVAILABLE | 503 | AI 服务不可用 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

---

## Authentication

所有端点需要用户已登录（Flask session）。未登录时返回 401。

```python
@ai_assistant_bp.before_request
def require_login():
    if 'user_id' not in session:
        return jsonify({
            'status': 'error',
            'error': {'code': 'UNAUTHORIZED', 'message': '请先登录'}
        }), 401
```
