# API Contracts: 前端导航架构重构

**Feature**: 前端导航架构重构
**Date**: 2025-01-21
**Phase**: 1 - Design

## Overview

本功能主要涉及前端模板和路由变更，新增 2 个统计相关 API。

## New Endpoints

### 1. 获取统计数据汇总

```http
GET /api/stats/summary
```

**Description**: 获取仪表盘统计数据，包括班级数、学生数、批改核心数、待处理任务数，以及最近活动

**Authentication**: Required (Session-based)

**Request Headers**:
```
X-Requested-With: SPA
Accept: application/json
```

**Response** (200 OK):
```json
{
  "class_count": 5,
  "student_count": 120,
  "grader_count": 3,
  "pending_task_count": 2,
  "recent_classes": [
    {
      "id": 1,
      "name": "Linux 期末考试",
      "course": "操作系统",
      "created_at": "2025-01-20T10:30:00",
      "created_at_relative": "2 小时前"
    }
  ],
  "recent_graders": [
    {
      "id": "linux_final_2026",
      "name": "Linux 期末考试(宽松模式)",
      "created_at": "2025-01-19T15:45:00",
      "created_at_relative": "1 天前"
    }
  ]
}
```

**Response** (401 Unauthorized):
```json
{
  "error": "Unauthorized",
  "message": "请先登录"
}
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 401 | 未登录 |
| 500 | 服务器错误 |

### 2. 刷新统计数据

```http
POST /api/stats/refresh
```

**Description**: 手动刷新会话缓存的统计数据

**Authentication**: Required (Session-based)

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**: None

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    // 同 GET /api/stats/summary
  }
}
```

## Modified Endpoints

### 1. 首页路由变更

```http
GET /
```

**Description**: 新的仪表盘首页（原班级列表内容迁移到 /tasks）

**Authentication**: Required

**Response**: HTML (dashboard.html)

**Template Variables**:
```python
{
  "stats": {
    "class_count": int,
    "student_count": int,
    "grader_count": int,
    "pending_task_count": int
  },
  "recent_classes": list,
  "recent_graders": list,
  "user": dict
}
```

### 2. 批改任务列表（新路由）

```http
GET /tasks
```

**Description**: 批改任务列表页面（原首页内容）

**Authentication**: Required

**Response**: HTML (tasks.html)

**Template Variables**:
```python
{
  "classes": [
    {
      "id": int,
      "name": str,
      "course": str,
      "strategy": str,
      "student_count": int,
      "graded_count": int,
      "created_at": str
    }
  ],
  "user": dict
}
```

## Frontend-Only Components

### SPA Navigation

所有页面支持 SPA 导航（通过 `spa_router.js`）：

**Request Headers** (自动添加):
```
X-Requested-With: SPA
Accept: text/html
```

**Response**: Full HTML document，SPA Router 提取 `#spa-content` 区域

### Sidebar Menu Structure

侧边栏菜单链接映射：

| 菜单项 | URL | 路由 |
|--------|-----|------|
| 仪表盘 | `/` | `main.index` |
| 批改任务 | `/tasks` | `main.tasks` (新增) |
| 新建班级 | `/new_class` | `grading.new_class` |
| 生成核心 | `/ai_generator` | `ai_gen.ai_generator_page` |
| 核心列表 | `/ai_core_list` | `ai_gen.ai_core_list_page` |
| 学生名单 | `/student/` | `student.list_page` |
| 导入学生 | `/student/import` | `student.import_page` |
| 文档库 | `/library/view` | `library.index` |
| 文件管理 | `/file_manager` | `library.file_manager_page` |
| 教务系统同步 | `/jwxt/view` | `jwxt.page_connect` |

## WebSocket / SSE (无)

本功能不涉及实时推送。通知轮询使用现有 `notification_center.html` 中的 `setInterval` 机制。

## OpenAPI Specification

### /api/stats/summary

```yaml
openapi: 3.0.0
info:
  title: AI Grading System API
  version: 1.0.0
paths:
  /api/stats/summary:
    get:
      summary: 获取统计数据汇总
      tags:
        - Statistics
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StatsSummary'
        '401':
          description: 未授权
components:
  schemas:
    StatsSummary:
      type: object
      properties:
        class_count:
          type: integer
        student_count:
          type: integer
        grader_count:
          type: integer
        pending_task_count:
          type: integer
        recent_classes:
          type: array
          items:
            $ref: '#/components/schemas/RecentClass'
        recent_graders:
          type: array
          items:
            $ref: '#/components/schemas/RecentGrader'
    RecentClass:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        course:
          type: string
        created_at:
          type: string
          format: date-time
        created_at_relative:
          type: string
    RecentGrader:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        created_at:
          type: string
          format: date-time
        created_at_relative:
          type: string
```
