# Quickstart: 成绩导出选择弹窗

**Feature**: 004-score-export-modal
**Date**: 2026-01-26

## 快速开始

### 前置条件

1. 已安装 Python 3.9+ 和项目依赖
2. 已创建至少一个班级并完成批改（有成绩数据）
3. 主应用运行在端口 5010

### 启动服务

```bash
# 安装依赖（如果尚未安装）
pip install -r requirements.txt

# 启动主应用
python app.py
```

### 功能验证步骤

#### 1. 打开批改任务页面

访问 `http://localhost:5010/grading/<class_id>`，其中 `<class_id>` 为已批改的班级ID。

#### 2. 点击"导出成绩"按钮

在页面右上角找到绿色的"导出成绩"按钮，点击后应弹出导出选择弹窗。

#### 3. 验证弹窗功能

**测试导出到文档库**:
1. 选择"文档库"卡片（边框变为紫色高亮）
2. 点击"确认导出"按钮
3. 预期结果：显示成功消息，弹窗自动关闭
4. 访问 `http://localhost:5010/library` 查看新文档

**测试导出到Excel**:
1. 选择"Excel表格"卡片
2. 点击"确认导出"按钮
3. 预期结果：浏览器开始下载 Excel 文件

**测试关闭弹窗**:
1. 点击弹窗右上角 X 按钮，弹窗关闭
2. 点击弹窗外部灰色区域，弹窗关闭

### 验证清单

- [ ] 点击"导出成绩"按钮弹出选择弹窗
- [ ] 弹窗包含两个选项卡片：文档库、Excel表格
- [ ] 点击卡片可切换选中状态（高亮边框）
- [ ] 选择"文档库"并确认 → 成功消息 + 弹窗关闭
- [ ] 文档库中可见新生成的成绩文档
- [ ] 成绩文档包含元数据头部和学生成绩表格
- [ ] 选择"Excel表格"并确认 → 下载Excel文件
- [ ] Excel文件内容正确（学号、姓名、分数）
- [ ] 点击X或弹窗外部可关闭弹窗
- [ ] 无成绩数据时显示错误提示

### 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 弹窗不显示 | JavaScript错误 | 检查浏览器控制台 |
| 导出到文档库失败 | 无成绩数据 | 确保班级已完成批改 |
| Excel下载失败 | 权限问题 | 确保当前用户是班级创建者 |
| 文档库找不到新文档 | 分类问题 | 筛选"其他"类型文档 |

### API 手动测试

```bash
# 导出到文档库（需要有效session）
curl -X POST http://localhost:5010/api/export_to_library/1 \
  -H "Cookie: session=<your-session-cookie>"

# 预期成功响应
{
  "status": "success",
  "msg": "成绩已导出到文档库",
  "data": {
    "asset_id": 123,
    "filename": "2025-2026学年度第一学期-...-机考分数.md"
  }
}
```

### 相关文件

| 文件 | 说明 |
|------|------|
| `templates/grading.html` | 批改任务页面（含弹窗触发按钮） |
| `templates/components/export_choice_modal.html` | 导出选择弹窗组件 |
| `blueprints/grading.py` | 后端API端点 |
| `services/score_document_service.py` | 成绩文档生成服务 |
