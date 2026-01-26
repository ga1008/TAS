# Quickstart: 成绩导出与考核登分表完善

**Created**: 2026-01-26
**Feature**: [spec.md](./spec.md)

## Prerequisites

- Python 3.x 环境
- 已安装项目依赖 (`pip install -r requirements.txt`)
- 主应用运行中 (`python app.py`)
- AI 助手服务运行中 (`python ai_assistant.py`)
- 至少一个已批改的班级（有学生成绩数据）

## Quick Validation Steps

### Step 1: 验证大题过滤逻辑

1. 创建测试批改任务，评分细则包含大题和小题：
   - 第一大题 (30分)
     - 1.1 (10分)
     - 1.2 (20分)
   - 第二大题 (70分)
     - 2.1 (35分)
     - 2.2 (35分)

2. 完成批改后，系统自动生成成绩文档

3. 验证点：
   - [ ] 文档库显示新的"考核登分表"分类
   - [ ] 成绩文档在该分类下
   - [ ] Markdown 表格仅显示"第一大题"、"第二大题"列，不显示 1.1、1.2、2.1、2.2

### Step 2: 验证元数据结构

1. 打开成绩文档详情
2. 查看元数据 JSON

3. 验证点：
   - [ ] 包含 `question_scores` 数组
   - [ ] 每个元素有 `name` 和 `max_score`
   - [ ] 包含 `total_max_score` 字段

```json
// 期望结构
{
  "question_scores": [
    {"name": "第一大题", "max_score": 30},
    {"name": "第二大题", "max_score": 70}
  ],
  "total_max_score": 100
}
```

### Step 3: 验证文档库选项卡

1. 访问文档库页面 `/library/view`
2. 查看顶部选项卡

3. 验证点：
   - [ ] 选项卡顺序：全部 → 教学大纲 → 考核计划 → 评分细则 → **考核登分表** → 期末试卷 → 其他
   - [ ] 点击"考核登分表"可筛选出成绩文档

### Step 4: 验证动态导出表单

1. 打开一个成绩文档详情
2. 点击"导出为 Excel"

3. 验证点：
   - [ ] 弹出表单显示独立的分值输入框（每个大题一个）
   - [ ] 输入框预填元数据中的 max_score 值
   - [ ] 可修改分值后导出

### Step 5: 验证分数编辑功能 (P2)

1. 在成绩文档详情页
2. 点击某学生的大题分数单元格
3. 修改分数并保存

4. 验证点：
   - [ ] 总分自动重新计算
   - [ ] 刷新后分数保持修改后的值

### Step 6: 回归测试

1. 验证现有功能不受影响：
   - [ ] 其他类型文档（试卷、评分细则等）可正常查看编辑
   - [ ] 批改流程正常工作
   - [ ] 旧成绩文档（doc_category='other'）仍可在"其他"分类下找到

## Test Data Setup

如需快速创建测试数据，可执行：

```python
# 在 Python shell 中
from extensions import db
from services.score_document_service import ScoreDocumentService

# 假设 class_id=1, user_id=1
result = ScoreDocumentService.generate_from_class(1, 1)
print(f"生成成绩文档: {result}")
```

## Development Server

```bash
# 终端 1: 主应用
python app.py

# 终端 2: AI 助手
python ai_assistant.py

# 访问
http://127.0.0.1:5010/library/view
```

## Debug Tips

- 查看生成的 meta_info：
  ```sql
  SELECT id, original_name, doc_category, meta_info
  FROM file_assets
  WHERE doc_category = 'score_sheet'
  ORDER BY id DESC LIMIT 5;
  ```

- 查看某班级的成绩详情：
  ```sql
  SELECT g.student_id, s.name, g.score_details, g.total_score
  FROM grades g
  JOIN students s ON g.student_id = s.student_id AND g.class_id = s.class_id
  WHERE g.class_id = 1;
  ```
