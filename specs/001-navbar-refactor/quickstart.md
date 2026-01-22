# Quickstart: 侧边栏与顶栏导航系统重构

## TL;DR

禁用 SPA 路由 → 全页刷新导航 → 解决 JS 功能失常问题

## Quick Summary

| 问题 | 根因 | 解决方案 |
|------|------|----------|
| 导航后 JS 功能失常 | SPA 路由脚本执行机制缺陷 | 禁用 SPA，恢复全页刷新 |
| 菜单高亮不准确 | 客户端路径匹配问题 | 服务端 Jinja2 判断 |
| 顶栏按钮不一致 | 页面内自建操作栏 | 统一使用 block topbar |

## Key Files

```
核心改动:
├── static/js/spa_router.js       # 禁用拦截
└── templates/base.html           # 服务端菜单激活 + 加载指示器

新建组件:
└── templates/components/topbar/
    ├── ai_generator_topbar.html
    ├── ai_core_list_topbar.html
    ├── student_list_topbar.html
    ├── library_topbar.html
    ├── file_manager_topbar.html
    └── jwxt_topbar.html

需修改页面:
├── ai_generator.html
├── ai_core_list.html
├── student/list.html
├── library/index.html
├── file_manager.html
└── jwxt_connect.html
```

## Implementation Checklist

### Phase 1: Core Fix
- [x] 修改 `spa_router.js` 的 `shouldIntercept()` 返回 `false`
- [x] 验证侧边栏导航变为全页刷新

### Phase 2: Server-Side Menu
- [x] 修改 `base.html` 侧边栏链接添加 Jinja2 active 判断
- [ ] 验证各页面菜单高亮正确 (手动测试)

### Phase 3: Loading Indicator
- [x] 添加 `.page-loading-bar` CSS
- [x] 添加 `beforeunload` 事件监听
- [ ] 验证加载指示器显示/隐藏 (手动测试)

### Phase 4: Topbar Components
- [x] 创建 6 个新 topbar 组件
- [x] 修改 6 个页面使用 block topbar
- [x] 移除页面内重复的操作栏

### Phase 5: Testing
- [ ] 逐页验证 JS 功能正常 (手动测试)
- [ ] 验证浏览器后退/前进 (手动测试)
- [ ] 检查 DevTools Console 无 JS 错误 (手动测试)
- [ ] 验证顶栏按钮匹配页面 (手动测试)

## Start Here

1. 阅读 [research.md](./research.md) 了解根因分析
2. 阅读 [plan.md](./plan.md) 了解详细实施步骤
3. 从 `spa_router.js` 开始改动

## Key Code Snippets

### 禁用 SPA 拦截
```javascript
// static/js/spa_router.js (约第140行)
function shouldIntercept(link) {
    return false; // 禁用所有 SPA 拦截
}
```

### 服务端菜单激活
```html
<!-- templates/base.html 侧边栏 -->
<a href="{{ url_for('main.index') }}"
   class="nav-link {% if request.path == '/' %}active{% endif %}">
```

### 页面使用 topbar
```html
{% block topbar %}
    {% include 'components/topbar/xxx_topbar.html' %}
{% endblock %}
```

## References

- [spec.md](./spec.md) - 功能需求
- [research.md](./research.md) - 技术研究
- [plan.md](./plan.md) - 实施计划
