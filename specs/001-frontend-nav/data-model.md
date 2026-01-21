# Data Model: 前端导航架构重构

**Feature**: 前端导航架构重构
**Date**: 2025-01-21
**Phase**: 1 - Design

## Overview

本功能不涉及数据库结构变更。所有统计数据来自现有表结构，前端实体为展示组件。

## Existing Data Structures (Reference)

### Database Tables

| Table | Columns (Relevant) | Purpose |
|-------|---------------------|---------|
| `classes` | id, name, course, workspace_path, strategy, created_by | 班级信息 |
| `students` | id, student_id, name, class_id | 学生信息 |
| `ai_tasks` | id, name, status, grader_id, created_at, created_by | AI 生成任务 |
| `ai_models` | id, model_name, capability | AI 模型配置 |
| `users` | id, username, is_admin | 用户信息 |

### File System

| Path | Purpose |
|------|---------|
| `grading_core/graders/` | 批改脚本文件（.py） |

## Frontend Entities

### 1. StatsCard (统计卡片)

**Purpose**: 在仪表盘显示单个统计指标

**Attributes**:
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `icon` | string | FontAwesome 图标类名 | `"fas fa-chalkboard"` |
| `label` | string | 统计指标名称 | `"班级总数"` |
| `value` | number | 统计数值 | `5` |
| `color` | string | 卡片主题色 | `"indigo"` |
| `trend` | string | (可选) 趋势指示 | `"up"` / `"down"` |

**Validation Rules**:
- `value` >= 0
- `color` 必须是预定义主题色之一: indigo, sky, emerald, amber, rose

### 2. QuickAction (快捷操作入口)

**Purpose**: 仪表盘快捷操作卡片

**Attributes**:
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `icon` | string | FontAwesome 图标类名 | `"fas fa-plus"` |
| `title` | string | 操作标题 | `"新建班级"` |
| `description` | string | 操作描述 | `"创建新的批改班级"` |
| `url` | string | 跳转链接 | `"/new_class"` |
| `color` | string | 卡片主题色 | `"indigo"` |

**Validation Rules**:
- `url` 必须是有效的应用内路径
- `color` 必须是预定义主题色之一

### 3. ActivityItem (活动条目)

**Purpose**: 最近活动列表项

**Attributes**:
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `type` | string | 活动类型 | `"class_created"` / `"grader_generated"` |
| `title` | string | 活动标题 | `"Linux 期末考试班"` |
| `timestamp` | string | 相对时间 | `"2 小时前"` |
| `url` | string | 相关链接 | `"/grading/123"` |
| `icon` | string | 类型图标 | `"fas fa-chalkboard"` |

**Activity Types**:
| Type | Icon | Color | Description |
|------|------|-------|--------------|
| `class_created` | `fa-chalkboard` | `indigo` | 创建班级 |
| `grader_generated` | `fa-magic` | `purple` | 生成批改核心 |
| `grading_completed` | `fa-check` | `emerald` | 完成批改 |

### 4. BreadcrumbNode (面包屑节点)

**Purpose**: 面包屑导航层级节点

**Attributes**:
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `title` | string | 显示标题 | `"Linux 期末考试"` |
| `url` | string | (可选) 跳转链接 | `"/tasks"` |
| `isCurrent` | boolean | 是否当前位置 | `false` |

**Validation Rules**:
- 最后一个节点 `isCurrent = true`，`url = null`
- 其他节点 `isCurrent = false`，`url` 必须存在

## API Response Models

### GET /api/stats/summary

**Response Structure**:
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
      "created_at": "2025-01-20T10:30:00"
    }
  ],
  "recent_graders": [
    {
      "id": "linux_final_2026",
      "name": "Linux 期末考试(宽松模式)",
      "created_at": "2025-01-19T15:45:00"
    }
  ]
}
```

### GET /tasks

**Response**: HTML (由 tasks.html 模板渲染)

**Template Context**:
```python
{
  "classes": [
    {
      "id": 1,
      "name": "Linux 期末考试",
      "course": "操作系统",
      "strategy": "server_config_2025",
      "student_count": 30,
      "graded_count": 25
    }
  ],
  "user": {...}
}
```

### GET /

**Response**: HTML (由 dashboard.html 模板渲染)

**Template Context**:
```python
{
  "stats": {
    "class_count": 5,
    "student_count": 120,
    "grader_count": 3,
    "pending_task_count": 2
  },
  "recent_activities": [...],
  "user": {...}
}
```

## State Transitions

### Sidebar State

| State | Description | Transition |
|-------|-------------|------------|
| `expanded` | 侧边栏展开（默认） | 用户点击收起按钮 |
| `collapsed` | 侧边栏收起（图标模式） | 用户点击展开按钮 |
| `hidden` | 移动端侧边栏隐藏 | 用户点击汉堡菜单 |
| `overlay` | 移动端侧边栏覆盖显示 | 用户点击遮罩层/菜单项 |

### Topbar Context State

| Page | Topbar Component | Key Actions |
|------|-----------------|-------------|
| `/` | dashboard_topbar | 刷新、通知中心 |
| `/tasks` | tasks_topbar | 新建班级、搜索 |
| `/grading/<id>` | grading_topbar | 返回、导出、清空、删除 |
| `/ai_generator` | ai_generator_topbar | 查看核心列表、通知 |

## No Database Changes

本功能不需要数据库迁移。所有数据来自现有表结构，仅添加聚合查询方法。
