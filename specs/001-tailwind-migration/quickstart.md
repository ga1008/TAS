# Quickstart: Frontend Tailwind CSS Migration

**Feature**: 001-tailwind-migration
**Date**: 2026-01-22

## Prerequisites

- 项目已运行在本地开发环境
- 浏览器开发者工具可用
- 截图工具准备就绪（用于视觉对比）

## Migration Workflow

### Step 0: Pre-Migration Screenshots

在开始迁移前，截取所有主要页面的参考截图：

```bash
# 需要截图的页面列表
- /                    # Dashboard
- /login               # Login page
- /admin/login         # Admin login
- /grading             # Grading console
- /ai-generator        # AI generator
- /library             # Document library
- /tasks               # Task list
- /export              # Export page
```

### Step 1: Centralize Tailwind Configuration

**目标**: 将所有 Tailwind 配置集中到 base.html

1. 打开 `templates/base.html`
2. 确保 Tailwind CDN 和配置在 `<head>` 中：

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          brand: {
            50: '#f0f9ff',
            100: '#e0f2fe',
            200: '#bae6fd',
            300: '#7dd3fc',
            400: '#38bdf8',
            500: '#0ea5e9',
            600: '#4f46e5',
          },
        },
        animation: {
          'fade-in': 'fadeIn 0.5s ease-out',
          'slide-up': 'slideUp 0.3s ease-out',
          'pulse-slow': 'pulse 3s infinite',
          'shake': 'shake 0.5s ease-in-out',
        },
        keyframes: {
          fadeIn: {
            '0%': { opacity: '0' },
            '100%': { opacity: '1' },
          },
          slideUp: {
            '0%': { transform: 'translateY(10px)', opacity: '0' },
            '100%': { transform: 'translateY(0)', opacity: '1' },
          },
          shake: {
            '0%, 100%': { transform: 'translateX(0)' },
            '25%': { transform: 'translateX(-5px)' },
            '75%': { transform: 'translateX(5px)' },
          },
        },
      },
    },
  }
</script>
```

3. 移除其他页面中的重复 Tailwind 配置

### Step 2: Convert Core CSS Classes

**目标**: 将 style.css 中的类转换为 Tailwind

#### Glass Panel
```html
<!-- Before: class="glass-panel" -->
<!-- After: -->
<div class="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg border border-white/20">
```

#### Primary Button
```html
<!-- Before: class="btn btn-primary" -->
<!-- After: -->
<button class="bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-lg px-4 py-2 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300">
```

#### Form Input
```html
<!-- Before: class="form-control" -->
<!-- After: -->
<input class="w-full bg-white/50 border border-slate-200 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-300">
```

### Step 3: Convert AI Chat Styles

**目标**: 将 ai_chat.css 转换为 Tailwind

#### Chat FAB
```html
<!-- Before: class="ai-chat-fab" -->
<!-- After: -->
<button class="fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg z-50 bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:shadow-xl hover:scale-110 transition-all duration-300 flex items-center justify-center">
```

#### Chat Modal
```html
<!-- Before: class="ai-chat-modal" -->
<!-- After: -->
<div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
```

### Step 4: Update JavaScript Static Styles

**目标**: 将 chat-ui.js 中的静态样式转换为类操作

```javascript
// Before
element.style.display = 'none';
element.style.display = 'flex';

// After
element.classList.add('hidden');
element.classList.remove('hidden');
element.classList.add('flex');
```

### Step 5: Remove CSS File References

从 base.html 中移除：
```html
<!-- 删除这些行 -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/ai_chat.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/bootstrap.min.css') }}">
```

保留：
```html
<!-- 保留 FontAwesome -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/all.min.css') }}">
<!-- 保留 Bootstrap JS -->
<script src="{{ url_for('static', filename='js/bootstrap.bundle.min.js') }}"></script>
```

### Step 6: Delete Redundant Files

```bash
# 删除自定义 CSS
rm static/css/style.css
rm static/css/ai_chat.css

# 删除 Bootstrap CSS（保留 JS）
rm static/css/bootstrap*.css
rm static/css/bootstrap*.css.map
```

### Step 7: Validation

对每个页面执行：

1. **视觉对比**: 与 Step 0 的截图对比
2. **功能测试**:
   - 模态框打开/关闭
   - 工具提示显示
   - 表单提交
   - SPA 导航
3. **响应式测试**: 调整浏览器窗口大小
4. **控制台检查**: 无 CSS/JS 错误

## Common Issues & Solutions

### Issue: Bootstrap Modal Not Styled
**Solution**: 确保 modal 结构正确，添加 Tailwind 类：
```html
<div class="modal-dialog">
  <div class="modal-content bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl">
```

### Issue: Tooltip Not Visible
**Solution**: Bootstrap tooltip 需要初始化和样式：
```javascript
// 初始化
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})
```

### Issue: Backdrop-filter Not Working
**Solution**: 检查浏览器兼容性，添加降级：
```html
<div class="bg-white/70 backdrop-blur-xl supports-[backdrop-filter]:bg-white/70 bg-white/90">
```

## Rollback Procedure

如果迁移出现问题：

1. Git 回滚到迁移前的提交
2. 或者恢复删除的 CSS 文件
3. 恢复 base.html 中的 CSS 引用

## Success Criteria Checklist

- [ ] 所有页面视觉效果与迁移前一致
- [ ] Tailwind 配置只在 base.html 中存在
- [ ] static/css 目录只剩 all.min.css
- [ ] 所有 Bootstrap JS 组件正常工作
- [ ] 所有表单和导航功能正常
- [ ] 无控制台错误
- [ ] 页面加载时间可接受
