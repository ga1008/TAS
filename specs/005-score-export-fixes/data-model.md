# Data Model: 成绩导出与考核登分表完善

**Created**: 2026-01-26
**Feature**: [spec.md](./spec.md)

## Entity Changes

### E-001: file_assets 表 (现有表，无结构变更)
扩展 `doc_category` 字段的合法值，新增 `score_sheet`。

```sql
-- 现有字段
doc_category TEXT DEFAULT 'exam'
-- 新增合法值: 'score_sheet' (考核登分表)

-- doc_category 合法值:
-- 'exam' (试卷), 'standard' (评分细则), 'syllabus' (教学大纲),
-- 'plan' (考核计划), 'student_list' (学生名单),
-- 'score_sheet' (考核登分表), 'other' (其他)
```

### E-002: meta_info JSON 结构扩展
成绩文档 (score_sheet) 的 meta_info 字段增加两个新键：

```json
{
  "course_name": "Python程序设计",
  "class_name": "软工2401班",
  "teacher": "张老师",
  "academic_year_semester": "2025-2026学年度第一学期",
  "source_class_id": 123,
  "generated_at": "2026-01-26T10:30:00",
  "student_count": 45,
  "graded_count": 42,
  "average_score": 78.5,
  "pass_rate": 0.85,

  // 新增字段
  "question_scores": [
    {"name": "第一大题", "max_score": 30},
    {"name": "第二大题", "max_score": 40},
    {"name": "第三大题", "max_score": 30}
  ],
  "total_max_score": 100
}
```

**字段说明**:
- `question_scores`: 数组，每个元素包含大题名称和满分值
- `total_max_score`: 试卷/考核总分，优先从评分细则/试卷元数据提取，否则计算各大题满分之和

### E-003: grades 表 score_details 字段 (现有，无变更)
保持原有结构，存储所有题目（包括大小题）的分数：

```json
[
  {"name": "1.1", "score": 10},
  {"name": "1.2", "score": 8},
  {"name": "第一大题", "score": 18},
  {"name": "2.1", "score": 15},
  {"name": "2.2", "score": 20},
  {"name": "第二大题", "score": 35}
]
```

**注意**: score_details 保留所有数据，大题过滤在导出时进行，不修改原始数据。

## Document Type Configuration

### C-001: DocumentTypeConfig.TYPES 扩展

```python
# export_core/doc_config.py
TYPES = {
    "exam": "试卷",
    "standard": "评分细则",
    "syllabus": "教学大纲",
    "plan": "考核计划",
    "student_list": "学生名单",
    "score_sheet": "考核登分表"  # 新增
}
```

### C-002: DocumentTypeConfig.FIELD_SCHEMAS 扩展

```python
# export_core/doc_config.py
FIELD_SCHEMAS = {
    # ... 现有配置 ...

    "score_sheet": {
        "label": "考核登分表元数据",
        "fields": [
            {"key": "course_name", "label": "课程名称", "type": "text", "required": True},
            {"key": "course_code", "label": "课程编号", "type": "text"},
            {"key": "class_name", "label": "班级", "type": "text"},
            {"key": "teacher", "label": "授课教师", "type": "text"},
            {"key": "academic_year_semester", "label": "学年学期", "type": "text"},
            {"key": "total_max_score", "label": "卷面总分", "type": "number"},
            {"key": "question_scores", "label": "题目分值", "type": "readonly",
             "description": "大题分值信息（只读，从成绩数据自动生成）"}
        ]
    }
}
```

## Data Flow

### DF-001: 成绩导出流程 (修改)

```
批改完成
    ↓
ScoreDocumentService.generate_from_class()
    ↓
build_metadata()
    ├── 从 grades.score_details 提取大题 (过滤小题)
    ├── 计算各大题 max_score
    ├── 设置 question_scores 数组
    └── 设置 total_max_score (优先从试卷元数据获取)
    ↓
build_markdown_content()
    └── 表格列仅包含大题，不含小题
    ↓
db.save_score_document()
    └── doc_category = 'score_sheet' (而非 'other')
```

### DF-002: Excel 导出流程 (修改)

```
用户点击导出 Excel
    ↓
前端读取 meta_info.question_scores
    ↓
动态生成分值输入框 (每个大题一个)
    ↓
用户确认/修改分值
    ↓
调用 MachineTestScoreExporter.generate()
    └── form_data.questions_config = 动态生成的数组格式
```

## Migration Strategy

**无数据迁移**: 旧的成绩文档保持 `doc_category='other'`，仅新导出的文档使用 `'score_sheet'`。

**向后兼容**:
- 缺少 question_scores 的文档：Excel 导出时使用默认配置
- 缺少 total_max_score 的文档：计算各大题满分之和
