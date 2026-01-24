# API Contracts: AI Welcome System

**Feature**: 001-fix-ai-welcome
**Date**: 2025-01-25
**Status**: Documentation only (no API changes)

## Overview

This document describes the existing API endpoints used by the AI welcome system. **No API changes are required for this bug fix.**

## Endpoints

### GET /api/welcome/messages

Fetch AI-generated welcome messages for the current user.

**Request**:
```http
GET /api/welcome/messages?context={page_context}
Cookie: session=...
```

**Parameters**:
- `context` (string, optional): Page context for message generation
  - Values: `dashboard`, `tasks`, `student_list`, `ai_generator`, `export`

**Response**:
```json
{
  "success": true,
  "message": "早安，老师！今天有 3 个批改任务等待处理。",
  "cached": true,
  "generated_at": "2025-01-25T08:00:00Z"
}
```

**Error Response** (401 Unauthorized):
```json
{
  "success": false,
  "error": "未登录"
}
```

---

### POST /api/welcome/chat

Send a message to the AI assistant and receive a response.

**Request**:
```http
POST /api/welcome/chat
Content-Type: application/json
Cookie: session=...

{
  "message": "如何创建新班级？"
}
```

**Response**:
```json
{
  "success": true,
  "reply": "创建新班级很简单！点击左侧菜单的'新建任务'，然后...",
  "suggestions": [
    "导入学生名单",
    "设置批改参数"
  ]
}
```

---

### GET /api/welcome/fallback

Get fallback welcome message when AI service is unavailable.

**Request**:
```http
GET /api/welcome/fallback
```

**Response**:
```json
{
  "success": true,
  "message": "欢迎使用 TAS 教学辅助系统！",
  "is_fallback": true
}
```

## Notes

- All endpoints require user authentication (session cookie)
- Messages are cached in the database to reduce AI API calls
- Fallback messages are used when AI service is unavailable
