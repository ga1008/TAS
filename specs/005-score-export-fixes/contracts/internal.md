# Internal Contracts: 成绩导出与考核登分表完善

**Created**: 2026-01-26
**Feature**: [spec.md](../spec.md)

## Service Layer Contracts

### SC-001: ScoreDocumentService.generate_from_class()

**Location**: `services/score_document_service.py`

**Signature**:
```python
@staticmethod
def generate_from_class(class_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    批改完成后生成成绩文档到文档库

    Args:
        class_id: 班级 ID
        user_id: 触发生成的用户 ID

    Returns:
        {'asset_id': int, 'filename': str} 成功时
        None: 无成绩或生成跳过时

    Changes (005):
        - doc_category 从 'other' 改为 'score_sheet'
        - meta_info 增加 question_scores 和 total_max_score
        - Markdown 表格仅包含大题列
    """
```

### SC-002: ScoreDocumentService.aggregate_main_questions()

**Location**: `services/score_document_service.py` (新增)

**Signature**:
```python
@staticmethod
def aggregate_main_questions(score_details: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    从 score_details 中提取大题，聚合小题分数

    Args:
        score_details: 原始分项成绩列表 [{"name": "1.1", "score": 10}, ...]

    Returns:
        Tuple[main_questions, question_scores]:
        - main_questions: [{"name": "第一大题", "score": 30}, ...] 用于显示
        - question_scores: [{"name": "第一大题", "max_score": 30}, ...] 用于元数据
    """
```

### SC-003: is_main_question()

**Location**: `services/score_document_service.py` (新增)

**Signature**:
```python
def is_main_question(name: str) -> bool:
    """
    判断题目名称是否为大题

    大题规则:
    - 以中文数字开头 (一、二、三...)
    - 以 "第X" 格式开头 (第一、第二...)
    - 以 "任务X" 格式开头 (任务一、任务1...)

    小题规则:
    - 以阿拉伯数字开头 (1、2、1.1、2.1...)

    Args:
        name: 题目名称

    Returns:
        True if 大题, False if 小题
    """
```

## API Contracts

### API-001: GET /api/file_detail/<file_id>

**Location**: `blueprints/library.py`

**Response Changes (score_sheet documents)**:
```json
{
  "status": "success",
  "file": {
    "id": 123,
    "original_name": "2025-2026学年度第一学期-Python程序设计-软工2401班-机考分数.md",
    "doc_category": "score_sheet",
    "parsed_content": "| 序号 | 学号 | 姓名 | 第一大题 | 第二大题 | 总分 |\n...",
    "meta_info": {
      "course_name": "Python程序设计",
      "question_scores": [
        {"name": "第一大题", "max_score": 30},
        {"name": "第二大题", "max_score": 70}
      ],
      "total_max_score": 100
    }
  }
}
```

### API-002: POST /api/update_score_cell

**Location**: `blueprints/library.py` (新增)

**Description**: 更新学生某大题的分数

**Request**:
```json
{
  "asset_id": 123,
  "student_id": "202401001",
  "question_name": "第一大题",
  "new_score": 25
}
```

**Response**:
```json
{
  "status": "success",
  "new_total": 85,
  "msg": "分数已更新"
}
```

**Behavior**:
- 更新 grades 表对应记录的 score_details
- 重新计算该学生的 total_score
- 更新 file_assets 的 parsed_content (重新生成 Markdown)

### API-003: GET /api/export/score_sheet/<asset_id>/config

**Location**: `blueprints/export.py` (新增或修改)

**Description**: 获取 Excel 导出配置（动态字段）

**Response**:
```json
{
  "status": "success",
  "export_config": {
    "auto_fill": {
      "course_name": "Python程序设计",
      "course_code": "E020001B4",
      "class_name": "软工2401班",
      "teacher": "张老师"
    },
    "question_fields": [
      {"name": "第一大题", "label": "第一题", "default_value": 30},
      {"name": "第二大题", "label": "第二题", "default_value": 70}
    ],
    "total_score": 100
  }
}
```

## Frontend Contracts

### FC-001: Category Tabs Order

**Location**: `templates/library/index.html`

**Expected Order**:
```
全部 | 1. 教学大纲 | 2. 考核计划 | 3. 评分细则 | 8. 考核登分表 | 9. 期末试卷 | 其他资料
```

### FC-002: Dynamic Export Form

**Location**: `templates/components/export_modal.html` (或相关模板)

**Trigger**: 当导出 score_sheet 类型文档时

**Behavior**:
1. 调用 API-003 获取配置
2. 为 question_fields 中每个大题生成独立输入框
3. 预填 default_value，允许用户修改
4. 提交时将修改后的值传给导出 API

### FC-003: Score Sheet Detail View

**Location**: `templates/library/score_sheet_detail.html` (新增或扩展 index.html)

**Components**:
- 学生成绩表格（可编辑单元格）
- 元数据编辑区域
- Excel 导出按钮（fa-file-excel 图标）

## Database Contracts

### DB-001: doc_category 枚举扩展

**Table**: file_assets

**Valid Values**:
```
exam, standard, syllabus, plan, student_list, score_sheet, other
```

**No Migration Required**: 仅扩展允许值，不修改现有数据。
