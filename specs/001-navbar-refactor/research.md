# Technical Research: 侧边栏与顶栏导航系统重构

**Date**: 2026-01-22
**Spec**: [spec.md](./spec.md)
**Status**: Research Complete

## 1. Problem Statement

### 1.1 Core Bug Description

用户报告：通过侧边菜单导航到其他页面后，目标页面的 JavaScript 功能失常，常见错误如 "function is not defined"。

### 1.2 Root Cause Analysis

经过深入分析 `static/js/spa_router.js`，发现问题根源在于 SPA 路由的脚本执行机制。

#### SPA Router 工作流程

```
用户点击菜单 → fetch 目标页面 HTML → 解析 DOM
→ 替换 #spa-content innerHTML → executeScripts() → 更新菜单高亮
```

#### executeScripts() 函数问题 (spa_router.js:359-415)

```javascript
function executeScripts(container) {
    const scripts = container.querySelectorAll('script');
    scripts.forEach(oldScript => {
        const newScript = document.createElement('script');
        // 复制属性和内容...
        oldScript.parentNode.replaceChild(newScript, oldScript);
    });
}
```

**问题点**：

1. **执行顺序不确定**：`forEach` 遍历 + `replaceChild` 不保证脚本按原始顺序执行
2. **外部脚本跳过逻辑有漏洞**：已存在的脚本被跳过 (第376-388行)，但页面初始化函数可能在这些脚本中
3. **DOM Ready 事件失效**：`DOMContentLoaded` 不会重新触发，依赖此事件的初始化代码不会执行
4. **全局命名空间污染**：上一个页面的函数可能仍存在于全局 `window` 对象，导致调用错误版本
5. **module 脚本问题**：`type="module"` 脚本通过 replaceChild 重新执行可能失败

#### 受影响的页面初始化模式

各页面使用多种初始化模式，SPA 导航后可能失效：

| 页面 | 初始化模式 | SPA 兼容性 |
|------|-----------|------------|
| `student/list.html` | IIFE + DOMContentLoaded + spa:navigated | ✓ 部分兼容 |
| `dashboard.html` | 内联函数定义 | ✗ 可能覆盖冲突 |
| `ai_generator.html` | 组件脚本分散 | ✗ 依赖加载顺序 |
| `tasks.html` | 无初始化脚本 | ✓ 兼容 |

## 2. Current Architecture Analysis

### 2.1 Layout Structure (base.html)

```
┌─────────────────────────────────────────────────────────────────┐
│ app-sidebar (fixed, 260px)  │  app-topbar (fixed, 64px)        │
│                             │  {% block topbar %} ...           │
│ - 侧边导航菜单               │─────────────────────────────────────│
│ - 用户信息                   │  app-main (margin-left: 260px)    │
│                             │  ┌─ #spa-content ───────────────┐ │
│                             │  │ {% block content %}           │ │
│                             │  │ ...                           │ │
│                             │  └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Block Topbar Usage Survey

| 页面 | 使用 block topbar | 顶栏内容 |
|------|-------------------|----------|
| `dashboard.html` | ✓ 自定义 | 刷新数据 + 通知中心 (内嵌在页面，非独立组件) |
| `tasks.html` | ✓ include | tasks_topbar.html (新建任务 + 通知) |
| `ai_generator.html` | ✗ 默认 | 使用 base.html 默认顶栏 |
| `ai_core_list.html` | ✗ 默认 | 使用 base.html 默认顶栏 |
| `library/index.html` | ✗ 默认 | 页面内自建操作栏 |
| `file_manager.html` | ✗ 默认 | 页面内自建操作栏 |
| `student/list.html` | ✗ 默认 | 页面内自建操作栏 |
| `jwxt_connect.html` | ✗ 默认 | 页面内自建操作栏 |

**发现**：多数页面在页面内部自建了 "顶部操作栏" (`<div class="flex items-center justify-between mb-6">`)，与 block topbar 功能重复。

### 2.3 Existing Topbar Components

```
templates/components/topbar/
├── dashboard_topbar.html    # 仪表盘专用 (刷新数据 + 通知) - 未被 dashboard.html 使用
└── tasks_topbar.html        # 任务列表专用 (新建任务 + 通知) - 正常使用
```

## 3. Solution Evaluation

### 3.1 Option A: Fix SPA Script Execution

**方案**：增强 `executeScripts()` 函数，解决脚本执行问题。

**实现要点**：
- 按 DOM 顺序串行执行脚本
- 对 module 脚本使用动态 `import()`
- 触发自定义 DOM Ready 事件
- 页面卸载时清理全局函数

**代码示例**：
```javascript
async function executeScriptsOrdered(container) {
    const scripts = Array.from(container.querySelectorAll('script'));
    for (const oldScript of scripts) {
        await loadScript(oldScript);
    }
    container.dispatchEvent(new Event('spa:scripts-loaded'));
}
```

**评估**：
- 复杂度：高 (需要处理各种边缘情况)
- 风险：中 (可能引入新的兼容性问题)
- 维护成本：高 (每个新页面都需要验证)
- 性能收益：快速页面切换 (无全页刷新)

### 3.2 Option B: Disable SPA, Use Full Page Refresh ✓ RECOMMENDED

**方案**：禁用 SPA 路由器的链接拦截，恢复传统全页刷新导航。

**实现要点**：
- 修改 `spa_router.js` 的 `shouldIntercept()` 函数，始终返回 `false`
- 或者直接不加载 `spa_router.js`
- 侧边栏链接正常使用 `<a href>` 跳转

**代码示例**：
```javascript
// 方案 B1: 禁用拦截
function shouldIntercept(link) {
    return false; // 禁用所有 SPA 拦截
}

// 方案 B2: 完全移除 SPA 路由器
// 从 base.html 移除 <script src="spa_router.js"></script>
```

**评估**：
- 复杂度：低 (一行代码改动)
- 风险：低 (浏览器原生导航机制，最稳定)
- 维护成本：无 (零额外维护)
- 性能影响：轻微 (全页刷新约 200-400ms，用户可接受)

### 3.3 Option C: Hybrid Approach (SPA + MPA)

**方案**：保留 SPA 路由用于简单页面，复杂页面使用全页刷新。

**实现要点**：
- 为复杂页面链接添加 `data-spa-ignore` 属性
- SPA 路由器已支持此属性 (spa_router.js:147)

**评估**：
- 复杂度：中 (需要逐页判断)
- 风险：中 (行为不一致可能困惑用户)
- 维护成本：中 (新页面需决定使用哪种模式)

## 4. Recommended Solution: Option B

**选择理由**：

1. **可靠性第一**：P1 需求明确要求 "页面功能 100% 可用"，全页刷新是唯一能保证的方案
2. **最小改动**：只需禁用 SPA 路由，无需大规模重构
3. **性能可接受**：现代浏览器全页刷新已足够快，配合加载指示器用户体验良好
4. **符合 Flask/Jinja2 架构**：传统 Web 应用架构本就不依赖 SPA
5. **零维护成本**：无需为新页面考虑 SPA 兼容性

## 5. Technical Decisions

### TD-001: Navigation Strategy
- **Decision**: 禁用 SPA 路由，恢复全页刷新
- **Rationale**: 可靠性 > 性能 (P1 需求)
- **Implementation**: 修改 `shouldIntercept()` 返回 `false`

### TD-002: Topbar Architecture
- **Decision**: 继续使用 `{% block topbar %}` 模式
- **Rationale**: 已有模式成熟，无需引入新机制
- **Implementation**: 为缺少自定义顶栏的页面创建组件

### TD-003: Active Menu Highlighting
- **Decision**: 服务端确定激活状态 (使用 `request.path`)
- **Rationale**: 全页刷新后无需 JS 计算，更可靠
- **Implementation**: 在 base.html 侧边栏模板中使用 Jinja2 条件判断

### TD-004: Loading Indicator
- **Decision**: 使用 NProgress 风格的顶部进度条
- **Rationale**: 业界通用，用户熟悉，轻量级
- **Implementation**: CSS 动画 + JS 监听页面卸载事件

### TD-005: Error Handling
- **Decision**: 使用现有 `showToast()` 函数
- **Rationale**: 已在 base.html 中全局可用
- **Note**: 全页刷新模式下网络错误由浏览器处理，无需额外逻辑

### TD-006: Page-Specific Topbar Content
- **Decision**: 整合现有 "页面内操作栏" 到 block topbar
- **Rationale**: 统一设计，避免重复
- **Implementation**: 为每个页面创建专属 topbar 组件

## 6. Files Impact Analysis

### 6.1 Must Modify

| 文件 | 改动 | 原因 |
|------|------|------|
| `static/js/spa_router.js` | 禁用拦截 | 核心修复 |
| `templates/base.html` | 添加服务端菜单激活判断 + 加载指示器 | FR-016, FR-017 |

### 6.2 Must Create (Topbar Components)

| 组件 | 按钮内容 | 对应 FR |
|------|----------|--------|
| `ai_generator_topbar.html` | 文档解析管理 + 核心列表 | FR-010 |
| `ai_core_list_topbar.html` | 生成新核心 + 回收站 | FR-011 |
| `student_list_topbar.html` | 创建新班级 | FR-012 |
| `library_topbar.html` | 上传文档 | FR-013 |
| `file_manager_topbar.html` | 返回文档库 | FR-014 |
| `jwxt_topbar.html` | 同步数据 | FR-015 |

### 6.3 Must Verify/Update Page Templates

| 页面模板 | 操作 |
|---------|------|
| `dashboard.html` | 保留现有自定义 topbar (已OK) |
| `tasks.html` | 保留现有 include (已OK) |
| `ai_generator.html` | 添加 block topbar，移除页面内操作栏 |
| `ai_core_list.html` | 添加 block topbar，移除页面内操作栏 |
| `student/list.html` | 添加 block topbar，移除页面内操作栏 |
| `library/index.html` | 添加 block topbar，移除页面内操作栏 |
| `file_manager.html` | 添加 block topbar，移除页面内操作栏 |
| `jwxt_connect.html` | 添加 block topbar |

## 7. Testing Strategy

### 7.1 Functional Tests
1. 从首页通过侧边栏访问每个页面
2. 验证每个页面的核心功能 (按钮点击、表单提交、AJAX 请求)
3. 检查 DevTools Console 无 JS 错误

### 7.2 Navigation Tests
1. 浏览器后退/前进按钮正常工作
2. 直接输入 URL 访问页面正常
3. 快速连续点击不同菜单项无异常

### 7.3 Visual Tests
1. 侧边栏当前页面菜单项高亮正确
2. 顶栏按钮与当前页面匹配
3. 加载指示器在页面切换时显示

## 8. Rollback Plan

如果禁用 SPA 路由后发现不可预见的问题：

1. 恢复 `shouldIntercept()` 函数原逻辑
2. 或恢复 `spa_router.js` 原始文件
3. SPA 路由代码保留不删除，方便回滚

## 9. References

- [spec.md](./spec.md) - 功能需求规格
- [FRONTEND_GUIDE.md](../../templates/FRONTEND_GUIDE.md) - 前端设计规范
- [constitution.md](../../.specify/memory/constitution.md) - 项目架构宪法
