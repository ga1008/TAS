# Feature Specification: Frontend Tailwind CSS Migration

**Feature Branch**: `001-tailwind-migration`
**Created**: 2026-01-22
**Status**: Draft
**Input**: User description: "将前端样式全部迁移到 Tailwind CSS，统一样式配置，清理冗余文件"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent Visual Experience After Migration (Priority: P1)

教师或管理员访问系统的任何页面时，页面外观和交互效果与迁移前完全一致，没有视觉差异或功能缺失。

**Why this priority**: 这是迁移的核心目标——在不改变用户体验的前提下统一技术栈。任何视觉回归都会影响用户信任。

**Independent Test**: 可以通过对比迁移前后的页面截图，逐页验证视觉一致性。

**Acceptance Scenarios**:

1. **Given** 用户访问仪表盘页面, **When** 页面加载完成, **Then** 所有卡片、统计数据、欢迎消息的样式与迁移前一致
2. **Given** 用户打开 AI 聊天窗口, **When** 发送消息并收到回复, **Then** 消息气泡、代码高亮、复制按钮等功能正常工作
3. **Given** 用户在任意表单页面, **When** 填写并提交表单, **Then** 输入框、按钮、验证提示的样式和交互与迁移前一致
4. **Given** 用户使用 SPA 导航, **When** 点击侧边栏菜单项, **Then** 页面平滑过渡，加载动画正常显示

---

### User Story 2 - Unified Tailwind Configuration (Priority: P1)

开发者维护前端代码时，所有 Tailwind 配置集中在一处，不再需要在多个模板中重复配置。

**Why this priority**: 消除配置重复是本次重构的核心技术目标，直接影响代码可维护性。

**Independent Test**: 检查所有模板文件，确认 Tailwind 配置只在 base.html 中定义一次。

**Acceptance Scenarios**:

1. **Given** 开发者查看 base.html, **When** 搜索 Tailwind 配置, **Then** 找到唯一的集中配置块，包含所有自定义颜色、动画、关键帧
2. **Given** 开发者查看任意子页面模板, **When** 搜索 `tailwind.config`, **Then** 不存在任何 Tailwind 配置代码
3. **Given** 开发者需要修改主题颜色, **When** 只修改 base.html 中的配置, **Then** 所有页面自动应用新颜色

---

### User Story 3 - Removal of Redundant Style Files (Priority: P2)

项目中不再包含未使用的 CSS、JS、字体文件，代码库保持整洁。

**Why this priority**: 清理冗余文件可减少项目体积和维护负担，但不影响功能，优先级次于功能保持。

**Independent Test**: 运行静态分析工具或手动检查，确认所有保留的文件都被实际引用。

**Acceptance Scenarios**:

1. **Given** 迁移完成后, **When** 检查 static/css 目录, **Then** 只保留必要的 CSS 文件（如 FontAwesome 的 all.min.css）
2. **Given** 迁移完成后, **When** 检查 static/js 目录, **Then** 所有 JS 文件都被至少一个页面引用
3. **Given** 迁移完成后, **When** 检查 static/fonts 目录, **Then** 只保留 FontAwesome 字体文件

---

### User Story 4 - Bootstrap JS Components Continue Working (Priority: P2)

依赖 Bootstrap JS 的组件（模态框、工具提示、弹出框）在移除 Bootstrap CSS 后仍能正常工作。

**Why this priority**: 这些组件是系统交互的重要部分，但可以通过 Tailwind 样式替代 Bootstrap CSS。

**Independent Test**: 逐一测试所有使用 Bootstrap JS 的组件。

**Acceptance Scenarios**:

1. **Given** 用户点击触发模态框的按钮, **When** 模态框打开, **Then** 模态框正确显示，背景遮罩正常，关闭按钮可用
2. **Given** 用户悬停在带有 tooltip 的元素上, **When** tooltip 显示, **Then** tooltip 内容正确，位置准确
3. **Given** 管理员登录模态框, **When** 输入凭据并提交, **Then** 表单验证和提交流程正常工作

---

### User Story 5 - Python Backend Rendered Frontend Code Updated (Priority: P2)

后端 Python 文件中返回的 HTML/CSS 代码也使用 Tailwind 类名，保持风格统一。

**Why this priority**: 确保动态生成的内容与静态模板风格一致。

**Independent Test**: 搜索所有 Python 文件中的 HTML 字符串，验证使用 Tailwind 类名。

**Acceptance Scenarios**:

1. **Given** AI 生成器返回代码片段, **When** 代码渲染到页面, **Then** 样式与页面其他部分一致
2. **Given** 后端返回错误消息 HTML, **When** 消息显示在页面, **Then** 使用 Tailwind 的警告/错误样式类

---

### Edge Cases

- 页面在无网络环境下加载时，Tailwind CDN 不可用如何处理？（假设：系统需要网络连接，CDN 不可用时显示基础样式）
- 浏览器不支持 backdrop-filter 时，玻璃态效果如何降级？（假设：提供纯色背景作为降级方案）
- 自定义 CSS 与 Tailwind 类名冲突时如何处理？（假设：Tailwind 类名优先，自定义 CSS 使用更高特异性选择器）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 将所有页面样式统一使用 Tailwind CSS 实现
- **FR-002**: 系统 MUST 在 base.html 中集中定义唯一的 Tailwind 配置
- **FR-003**: 系统 MUST 保留 Tailwind 无法实现的样式在 `<style>` 标签中作为补充
- **FR-004**: 系统 MUST 移除 Bootstrap CSS 文件，仅保留 Bootstrap JS Bundle
- **FR-005**: 系统 MUST 保留 FontAwesome 图标库（all.min.css 和字体文件）
- **FR-006**: 系统 MUST 删除不再使用的 style.css 和 ai_chat.css 文件
- **FR-007**: 系统 MUST 将 style.css 中的玻璃态、按钮、卡片等样式转换为 Tailwind 类
- **FR-008**: 系统 MUST 将 ai_chat.css 中的聊天界面样式转换为 Tailwind 类
- **FR-009**: 系统 MUST 更新所有 HTML 模板使用 Tailwind 类名
- **FR-010**: 系统 MUST 更新 Python 文件中返回的 HTML 代码使用 Tailwind 类名
- **FR-011**: 系统 MUST 保持所有现有功能和页面元素不变
- **FR-012**: 系统 MUST 遵循 FRONTEND_GUIDE.md 中定义的设计规范
- **FR-013**: 系统 MUST 保持 SPA 路由和页面过渡效果正常工作
- **FR-014**: 系统 MUST 保持响应式布局在各种屏幕尺寸下正常显示

### Key Entities

- **HTML 模板文件**: templates/ 目录下的所有 .html 文件，包括 base.html、页面模板、组件模板
- **CSS 文件**: static/css/ 目录下的样式文件，需要评估保留或删除
- **JS 文件**: static/js/ 目录下的脚本文件，需要检查是否有内联样式需要更新
- **Python 蓝图文件**: blueprints/ 目录下返回 HTML 的 Python 文件
- **设计规范**: templates/FRONTEND_GUIDE.md 定义的设计准则

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 迁移后所有页面视觉效果与迁移前一致，无明显差异
- **SC-002**: Tailwind 配置在整个项目中只存在一处（base.html）
- **SC-003**: static/css 目录中只保留 all.min.css（FontAwesome）
- **SC-004**: 所有 Bootstrap 模态框、工具提示、弹出框功能正常
- **SC-005**: 所有表单提交、数据加载、SPA 导航功能正常
- **SC-006**: 页面加载时间不超过迁移前的 120%
- **SC-007**: 项目中不存在未被引用的 CSS/JS 文件

## Clarifications

### Session 2026-01-22

- Q: Should migration be done incrementally or all at once? → A: Incremental migration - convert one page/component at a time, validate, then proceed
- Q: How should visual consistency be verified? → A: Manual comparison - take before/after screenshots and visually compare each page

## Assumptions

- 迁移采用增量方式，逐页/逐组件转换并验证后再继续，便于回滚和问题定位
- 视觉一致性通过手动截图对比验证，迁移前先截取各页面参考图
- 系统继续使用 Tailwind CDN 模式，不引入构建流程
- Bootstrap JS Bundle 保留用于模态框等组件
- FontAwesome 图标库保留不变
- 设计风格遵循现有的玻璃态/新拟态混合风格
- 浏览器兼容性要求与现有系统一致
