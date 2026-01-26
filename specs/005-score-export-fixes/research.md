# Research: 成绩导出与考核登分表完善

**Created**: 2026-01-26
**Feature**: [spec.md](./spec.md)

## Technology Decisions

### TD-001: 大题/小题识别规则
**Decision**: 使用中文数字前缀规则
- **大题**: 题目名称以中文数字（一、二、三）或"第X"格式开头
- **小题**: 题目名称以阿拉伯数字开头（1、2、1.1、2.1等）

**Rationale**: 符合中国高校考核的命名习惯，大题通常为"第一大题"、"任务一"等，小题为"1.1"、"2.1"等。

**Implementation**:
```python
import re

def is_main_question(name: str) -> bool:
    """判断是否为大题"""
    # 中文数字: 一、二、三...
    if re.match(r'^[一二三四五六七八九十]+', name):
        return True
    # "第X" 格式: 第一、第二...
    if re.match(r'^第[一二三四五六七八九十\d]+', name):
        return True
    # 任务X 格式: 任务一、任务1...
    if re.match(r'^任务[一二三四五六七八九十\d]+', name):
        return True
    return False
```

### TD-002: 新文档分类 score_sheet
**Decision**: 新增 `score_sheet` 分类，位于 `standard` 和 `exam` 之间

**Current Order**: all → syllabus → plan → standard → exam → other
**New Order**: all → syllabus → plan → standard → **score_sheet** → exam → other

**Implementation Points**:
- `export_core/doc_config.py`: 添加 `score_sheet` 到 `TYPES` 和 `FIELD_SCHEMAS`
- `templates/library/index.html`: 在 categoryTabs 中添加新选项卡
- `services/score_document_service.py`: 将 `doc_category: 'other'` 改为 `'score_sheet'`

### TD-003: 动态题目分值表单
**Decision**: 从 meta_info.question_scores 读取大题信息，动态生成表单字段

**Current Implementation** (`MachineTestScoreExporter.UI_SCHEMA`):
```python
{"name": "questions_config", "label": "题目分值配置", "type": "text",
 "placeholder": "格式：题号:分值，用逗号分隔。例：一:20,二:30,三:20,四:30"}
```

**New Implementation**:
```python
# 动态字段由前端根据 meta_info.question_scores 生成
# 后端接收数组格式: [{"name": "一", "score": 20}, ...]
```

## Existing Code Analysis

### Score Export Flow
```
批改完成 → ScoreDocumentService.generate_from_class()
         ↓
       build_metadata()     → 从 class/ai_tasks/file_assets 追溯元数据
         ↓
       build_markdown_content() → 生成成绩表格 Markdown
         ↓
       db.save_score_document() → 保存到 file_assets 表
```

**Key File**: `services/score_document_service.py`
- Line 62: `'doc_category': 'other'` → 需改为 `'score_sheet'`
- Line 193-252: `build_markdown_content()` → 需过滤小题，仅保留大题

### Grades Table Structure
```sql
grades (
    student_id TEXT,
    class_id INTEGER,
    total_score REAL,
    score_details TEXT,  -- JSON: [{"name": "1.1", "score": 10}, {"name": "第一大题", "score": 30}, ...]
    ...
)
```

### File Assets Table Structure
```sql
file_assets (
    id INTEGER PRIMARY KEY,
    doc_category TEXT DEFAULT 'exam',
    parsed_content TEXT,      -- Markdown 成绩表
    meta_info TEXT,           -- JSON 元数据
    ...
)
```

### Document Type Config
**File**: `export_core/doc_config.py`
```python
TYPES = {
    "exam": "试卷",
    "standard": "评分细则",
    "syllabus": "教学大纲",
    "plan": "考核计划",
    "student_list": "学生名单"
}
```
需添加: `"score_sheet": "考核登分表"`

### Library Template Tabs
**File**: `templates/library/index.html` (Line 115-122)
```html
<button data-cat="all">全部</button>
<button data-cat="syllabus">1. 教学大纲</button>
<button data-cat="plan">2. 考核计划</button>
<button data-cat="standard">3. 评分细则</button>
<!-- 此处插入: score_sheet (8. 考核登分表) -->
<button data-cat="exam">9. 期末试卷</button>
<button data-cat="other">其他资料</button>
```

## API Endpoints Analysis

### Existing Endpoints (blueprints/library.py)
- `GET /api/library/files` - 文档列表筛选
- `GET /api/file_detail/<file_id>` - 文档详情
- `POST /api/update_file_content` - 更新内容
- `POST /api/update_file_metadata` - 更新元数据

### Excel Export (blueprints/export.py)
需研究现有导出流程，添加动态字段支持

## Questions Resolved

| Question | Answer | Source |
|----------|--------|--------|
| 大题识别规则 | 中文数字/"第X"前缀=大题，阿拉伯数字=小题 | Spec Clarification |
| 编辑分数后总分 | 自动计算各大题之和 | Spec Clarification |
| 旧文档迁移 | 不迁移，保持 doc_category='other' | Spec Clarification |

## Risk Assessment

### Low Risk
- 新增 score_sheet 分类：纯增量，不影响现有文档
- 修改 categoryTabs 顺序：纯 UI 变更

### Medium Risk
- 修改 build_markdown_content() 过滤逻辑：需确保不破坏现有成绩数据
- 动态表单字段：需前后端协调

### Mitigation
- 为 build_markdown_content() 添加单元测试
- 动态表单前端实现参考现有 doc_config.py 的 FIELD_SCHEMAS 模式
