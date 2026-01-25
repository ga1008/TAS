# Data Model: 成绩导出选择弹窗

**Feature**: 004-score-export-modal
**Date**: 2026-01-26

## 概述

本功能不引入新的数据模型，完全复用现有的数据库表结构。以下是涉及的现有实体及其在本功能中的角色。

## 现有实体复用

### 1. file_assets (成绩文档存储)

**角色**: 存储导出到文档库的成绩Markdown文档

| 字段 | 类型 | 说明 | 本功能用途 |
|------|------|------|------------|
| id | INTEGER | 主键 | - |
| file_hash | TEXT | 文件唯一哈希 | 由 `class_id:timestamp:content` 生成 |
| original_name | TEXT | 原始文件名 | `{学年学期}-{课程}-{班级}-机考分数.md` |
| file_size | INTEGER | 文件大小 | Markdown内容字节数 |
| physical_path | TEXT | 物理路径 | NULL (纯Markdown内容) |
| parsed_content | TEXT | 解析后内容 | 完整的Markdown成绩表格 |
| meta_info | TEXT (JSON) | 元数据 | 包含 source_class_id, teacher, course_code 等 |
| doc_category | TEXT | 文档类型 | 固定为 "other" |
| course_name | TEXT | 课程名称 | 从班级记录获取 |
| source_class_id | INTEGER | 来源班级ID | 用于Excel导出模板查询成绩 |
| uploaded_by | INTEGER | 上传用户ID | 当前用户ID |
| created_at | TIMESTAMP | 创建时间 | 自动生成 |

### 2. classes (班级信息)

**角色**: 提供课程名称、班级名称、批改策略

| 字段 | 类型 | 本功能用途 |
|------|------|------------|
| id | INTEGER | 班级ID |
| name | TEXT | 班级名称 |
| course | TEXT | 课程名称 |
| strategy | TEXT | 批改策略 (grader_id) → 追溯元数据 |
| created_by | INTEGER | 创建者 → 权限验证 |

### 3. grades (学生成绩)

**角色**: 提供学生分数数据

| 字段 | 类型 | 本功能用途 |
|------|------|------------|
| class_id | INTEGER | 关联班级 |
| student_id | TEXT | 学号 |
| total_score | REAL | 总分 |
| score_details | TEXT (JSON) | 各题分数 |
| status | TEXT | 批改状态 |

### 4. students (学生信息)

**角色**: 提供学生姓名、性别

| 字段 | 类型 | 本功能用途 |
|------|------|------------|
| student_id | TEXT | 学号 |
| name | TEXT | 姓名 |
| gender | TEXT | 性别 |
| class_id | INTEGER | 关联班级 |

### 5. ai_tasks (批改任务)

**角色**: 元数据追溯链中间环节

| 字段 | 类型 | 本功能用途 |
|------|------|------------|
| grader_id | TEXT | 批改器ID ← class.strategy |
| exam_path | TEXT | 试卷路径 → file_assets |

## 元数据追溯链

```
classes.strategy (grader_id)
       ↓
ai_tasks (WHERE grader_id = ?)
       ↓
ai_tasks.exam_path
       ↓
file_assets (WHERE physical_path = ? OR original_name = ?)
       ↓
file_assets.meta_info (JSON)
       ↓
提取: teacher, course_code, academic_year_semester
```

## 成绩文档 meta_info 结构

```json
{
  "course_name": "Python程序设计",
  "class_name": "23级软件工程1班",
  "source_class_id": 42,
  "generated_at": "2026-01-26T10:30:00",
  "teacher": "张三",
  "course_code": "E020001B4",
  "academic_year_semester": "2025-2026学年度第一学期",
  "student_count": 45,
  "graded_count": 43,
  "average_score": 78.5,
  "pass_rate": 0.88
}
```

## 数据流图

```
用户点击"导出到文档库"
        ↓
前端 POST /api/export_to_library/{class_id}
        ↓
ScoreDocumentService.generate_from_class(class_id, user_id)
        ↓
    ┌─────────────────┐
    │ build_metadata  │ ← classes, ai_tasks, file_assets
    └─────────────────┘
        ↓
    ┌───────────────────────┐
    │ build_markdown_content │ ← students, grades
    └───────────────────────┘
        ↓
    ┌───────────────────────┐
    │ save_score_document   │ → file_assets INSERT
    └───────────────────────┘
        ↓
返回 {status: success, asset_id, filename}
```

## 无需新增表或字段

本功能完全基于现有数据模型实现，无需数据库迁移。
