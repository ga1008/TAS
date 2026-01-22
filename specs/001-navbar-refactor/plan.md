# Implementation Plan: 侧边栏与顶栏导航系统重构

**Branch**: `001-navbar-refactor`
**Date**: 2026-01-22
**Spec**: [spec.md](./spec.md)
**Research**: [research.md](./research.md)

## Summary

重构侧边栏和顶栏导航系统，解决页面切换后 JavaScript 功能失常问题。

**核心方案**：禁用 SPA 路由器，恢复传统全页刷新导航，同时统一各页面的顶栏按钮。

## Technical Context

- **Language/Version**: Python 3.x (Flask/Jinja2), JavaScript (jQuery + vanilla)
- **Primary Dependencies**: Flask, Jinja2, Tailwind CSS, jQuery 3.7.1, FontAwesome 6
- **Storage**: N/A (前端重构，不涉及数据库变更)
- **Testing**: Manual testing (导航功能验证、控制台错误检查)
- **Target Platform**: 现代浏览器 (Chrome, Firefox, Edge)
- **Project Type**: Flask Web 应用 (Jinja2 模板)
- **Performance Goals**: 页面切换感知延迟 < 500ms
- **Constraints**: 不引入新前端框架，保持现有技术栈

## Constitution Check

*GATE: Passed - Ready for implementation.*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 模块化解耦 | ✅ | 侧边栏/顶栏独立于页面内容，通过 block 机制实现 |
| II. 微服务分离 | ✅ | 不涉及 AI 微服务 |
| III. 前端设计一致性 | ✅ | 严格遵循 FRONTEND_GUIDE.md (玻璃按钮、动画反馈) |
| IV. 批改器可扩展性 | ✅ | 不涉及批改逻辑 |
| V. 数据库迁移友好 | ✅ | 不涉及数据库变更 |
| VI. AI 能力分层 | ✅ | 不涉及 AI 调用 |
| VII. AI 内容生成与缓存 | ✅ | 不涉及 AI 内容生成 |
| VIII. 前端 AI 内容展示 | ✅ | 顶栏保留 AI 欢迎语组件位置 |
| IX. 个性化AI交互 | ✅ | 不涉及 AI 交互变更 |

## Project Structure

### Documentation (this feature)

```text
specs/001-navbar-refactor/
├── plan.md              # This file
├── research.md          # Technical research and root cause analysis
├── quickstart.md        # Quick reference guide
├── spec.md              # Feature specification
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code Changes

```text
static/js/
└── spa_router.js              # MODIFY: 禁用 SPA 链接拦截

templates/
├── base.html                  # MODIFY: 服务端菜单激活 + 加载指示器
├── ai_generator.html          # MODIFY: 添加 block topbar
├── ai_core_list.html          # MODIFY: 添加 block topbar
├── file_manager.html          # MODIFY: 添加 block topbar
├── jwxt_connect.html          # MODIFY: 添加 block topbar
├── student/list.html          # MODIFY: 添加 block topbar
├── library/index.html         # MODIFY: 添加 block topbar
└── components/topbar/
    ├── dashboard_topbar.html  # EXISTS (unused by dashboard.html)
    ├── tasks_topbar.html      # EXISTS ✓
    ├── ai_generator_topbar.html    # CREATE
    ├── ai_core_list_topbar.html    # CREATE
    ├── student_list_topbar.html    # CREATE
    ├── library_topbar.html         # CREATE
    ├── file_manager_topbar.html    # CREATE
    └── jwxt_topbar.html            # CREATE
```

## Implementation Phases

### Phase 1: Core Navigation Fix

**目标**: 禁用 SPA 路由，恢复可靠的全页刷新导航

**文件**: `static/js/spa_router.js`

**改动**: 修改 `shouldIntercept()` 函数 (约第140行)
```javascript
function shouldIntercept(link) {
    return false; // 禁用所有 SPA 拦截
}
```

**验证**: 点击侧边栏菜单，浏览器地址栏更新，页面完整刷新

### Phase 2: Server-Side Active Menu

**目标**: 服务端确定菜单激活状态，取代 JS 计算

**文件**: `templates/base.html` (侧边栏部分)

**改动**: 使用 Jinja2 条件判断添加 active 类
```html
<a href="{{ url_for('main.index') }}"
   class="nav-link {% if request.path == '/' %}active{% endif %}">
    <i class="fas fa-chart-pie fa-fw"></i> 智教领航
</a>
```

**验证**: 刷新任意页面，对应菜单项高亮正确

### Phase 3: Loading Indicator

**目标**: 页面切换时显示顶部加载进度条

**文件**: `templates/base.html`

**改动**:
1. 添加 CSS 样式 (NProgress 风格)
2. 添加 HTML 元素 `<div class="page-loading-bar" id="page-loading-bar"></div>`
3. 添加 JS 监听 `beforeunload` 事件显示进度条

**验证**: 点击菜单后立即显示进度条，页面加载完成后消失

### Phase 4: Create Topbar Components

为每个缺少自定义顶栏的页面创建 topbar 组件：

| 组件 | 按钮内容 | 对应 FR |
|------|----------|--------|
| `ai_generator_topbar.html` | 文档解析管理 + 核心列表 + 通知 | FR-010 |
| `ai_core_list_topbar.html` | 生成新核心 + 回收站 + 通知 | FR-011 |
| `student_list_topbar.html` | 创建新班级 + 通知 | FR-012 |
| `library_topbar.html` | 上传文档 + 通知 | FR-013 |
| `file_manager_topbar.html` | 返回文档库 + 通知 | FR-014 |
| `jwxt_topbar.html` | 同步数据 + 通知 | FR-015 |

### Phase 5: Update Page Templates

修改各页面使用 `{% block topbar %}`：

```html
{% block topbar %}
    {% include 'components/topbar/xxx_topbar.html' %}
{% endblock %}
```

同时移除页面内重复的 `<div class="flex items-center justify-between mb-6">` 操作栏。

### Phase 6: Testing & Validation

**功能测试**:
- 从首页通过侧边栏访问每个页面
- 验证每个页面的核心功能 (按钮点击、表单提交、AJAX 请求)
- 检查 DevTools Console 无 JS 错误

**导航测试**:
- 浏览器后退/前进按钮正常工作
- 直接输入 URL 访问页面正常
- 快速连续点击不同菜单项无异常

**视觉测试**:
- 侧边栏当前页面菜单项高亮正确
- 顶栏按钮与当前页面匹配
- 加载指示器在页面切换时显示

## Success Criteria Mapping

| 成功标准 | 验证方法 |
|----------|----------|
| SC-001: 页面功能 100% 可用 | 逐页测试核心功能 |
| SC-002: 浏览器导航正常 | 后退/前进按钮测试 |
| SC-003: 顶栏按钮正确 | 视觉检查 |
| SC-004: 延迟 < 500ms | 主观感知确认 |
| SC-005: 无 JS 错误 | DevTools Console |
| SC-006: 菜单高亮正确 | 视觉检查 |

## Risk Assessment

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 全页刷新性能不如 SPA | 低 | 低 | 加载指示器提升感知 |
| 部分页面遗漏顶栏修改 | 中 | 低 | 系统性检查清单 |
| 破坏现有功能 | 低 | 高 | 逐页验证 + 回滚计划 |

## Rollback Plan

如果发现严重问题：

1. 恢复 `spa_router.js` 中 `shouldIntercept()` 函数原逻辑
2. 移除 base.html 中新增的加载指示器代码
3. 保留服务端菜单激活逻辑 (无副作用)
4. 回滚顶栏组件变更 (可选)

## Complexity Tracking

> 无 Constitution 违规，实施方案简单直接。

## References

- [spec.md](./spec.md) - 功能需求规格
- [research.md](./research.md) - 技术研究与决策
- [FRONTEND_GUIDE.md](../../templates/FRONTEND_GUIDE.md) - 前端设计规范
- [constitution.md](../../.specify/memory/constitution.md) - 项目架构宪法
