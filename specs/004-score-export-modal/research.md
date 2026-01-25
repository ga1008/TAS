# Research: 成绩导出选择弹窗

**Feature**: 004-score-export-modal
**Date**: 2026-01-26

## 1. 现有实现分析

### 1.1 ScoreDocumentService 服务

**位置**: `services/score_document_service.py`

**现有能力**:
- `generate_from_class(class_id, user_id)`: 从班级生成成绩文档
- `build_metadata(class_id)`: 构建元数据（包含元数据追溯逻辑）
- `build_markdown_content(class_id, metadata)`: 生成Markdown内容
- `_generate_filename(metadata)`: 生成文件名
- `_resolve_filename_conflict(class_id, base_name)`: 处理命名冲突

**Decision**: 直接复用现有服务，无需修改
**Rationale**: 服务已完整实现成绩文档生成逻辑，包括元数据追溯和命名冲突处理
**Alternatives considered**: 新建独立服务 - 拒绝，因为会造成代码重复

### 1.2 弹窗设计模式

**参考**: `templates/components/jwxt_login_modal.html`

**设计特点**:
- 使用 `fixed inset-0 z-[1050]` 全屏覆盖
- 背景使用 `bg-slate-900/40 backdrop-blur-md`
- 弹窗面板使用 `rounded-3xl bg-white/90 backdrop-blur-xl`
- 顶部彩色条 `h-1.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500`
- 状态管理使用 JavaScript 对象模式
- 动画使用 CSS `scale` 和 `opacity` 过渡

**Decision**: 采用相同的设计模式和动画效果
**Rationale**: 保持系统UI一致性，用户体验统一
**Alternatives considered**: Bootstrap Modal - 拒绝，因为项目使用 Tailwind CSS

### 1.3 grading.html 导出按钮

**当前实现** (grading.html:62-63):
```html
<a href="/export/{{ cls['id'] }}" class="...">导出成绩</a>
```

**修改方案**: 将 `<a>` 改为 `<button>` 并绑定弹窗打开事件

**Decision**: 修改为按钮触发弹窗
**Rationale**: 允许用户选择导出方式，而非直接跳转
**Alternatives considered**: 下拉菜单 - 拒绝，交互不如弹窗直观

## 2. API 设计

### 2.1 导出到文档库 API

**Endpoint**: `POST /api/export_to_library/<int:class_id>`

**Response**:
```json
// 成功
{"status": "success", "msg": "成绩已导出到文档库", "asset_id": 123, "filename": "2025-2026学年度第一学期-Python程序设计-23级软件工程1班-机考分数.md"}

// 失败 - 无成绩
{"status": "error", "msg": "暂无成绩数据可导出"}

// 失败 - 其他
{"status": "error", "msg": "导出失败: <详情>"}
```

**Decision**: 使用 POST 方法，返回 JSON 结果
**Rationale**: POST 适合创建资源操作，JSON 便于前端处理
**Alternatives considered**: GET + 重定向 - 拒绝，不适合异步操作反馈

### 2.2 Excel 导出

**Endpoint**: 保持现有 `GET /export/<int:class_id>`

**Decision**: 不修改现有导出逻辑
**Rationale**: 保持向后兼容，弹窗选择Excel时直接跳转

## 3. 前端交互设计

### 3.1 弹窗布局

```
+------------------------------------------+
|  [X]                                      |
|  ===================================      |
|         📊 导出成绩                        |
|    请选择导出方式                          |
|  -----------------------------------      |
|                                           |
|  +-------------+    +-------------+       |
|  | 📚 文档库   |    | 📑 Excel   |       |
|  | 导出为MD    |    | 直接下载    |       |
|  | 存入文档库  |    | 表格文件    |       |
|  +-------------+    +-------------+       |
|                                           |
|  [状态消息区域]                            |
|                                           |
|  -----------------------------------      |
|         [取消]      [确认导出]             |
+------------------------------------------+
```

**Decision**: 双卡片选择布局
**Rationale**: 直观展示两种选择，用户点击卡片选中，再点确认执行
**Alternatives considered**: Tab切换 - 拒绝，操作步骤更多；单选按钮 - 拒绝，视觉效果不佳

### 3.2 状态反馈

- 选中状态：卡片边框变为 `ring-2 ring-indigo-500`
- 加载状态：按钮显示旋转图标 + "导出中..."
- 成功状态：绿色消息框 + 自动关闭弹窗
- 失败状态：红色消息框 + 震动动画

**Decision**: 采用与 jwxt_login_modal 一致的状态反馈模式
**Rationale**: 用户熟悉的交互模式

## 4. 技术栈确认

| 组件 | 技术选择 | 备注 |
|------|----------|------|
| 弹窗结构 | Jinja2 组件 | `templates/components/export_choice_modal.html` |
| 样式 | Tailwind CSS | 复用现有 glass-panel 等类 |
| 状态管理 | JavaScript 对象 | 参考 JwxtModal 模式 |
| 动画 | CSS Transitions | scale + opacity |
| API调用 | Fetch API | 异步POST请求 |
| 后端 | Flask Blueprint | 在 grading.py 中添加 |

## 5. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 成绩数据量大导致导出慢 | 用户体验差 | 显示加载状态，前端不阻塞 |
| 元数据追溯失败 | 文档信息不完整 | 使用默认值和推断值 |
| 文件名冲突 | 覆盖旧文档 | 已有时间戳后缀机制 |
| 网络错误 | 导出失败 | 显示错误消息，允许重试 |

## 6. 结论

所有技术点已确认，无需进一步研究。可以直接进入 Phase 1 设计阶段。
