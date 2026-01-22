# Research: Frontend Tailwind CSS Migration

**Feature**: 001-tailwind-migration
**Date**: 2026-01-22

## Research Topics

### 1. Bootstrap CSS Removal with JS Components Retained

**Decision**: 移除所有 Bootstrap CSS 文件，仅保留 Bootstrap JS Bundle

**Rationale**:
- Bootstrap JS 组件（Modal、Tooltip、Popover）不依赖 Bootstrap CSS 的视觉样式
- JS 组件只需要正确的 HTML 结构和 data 属性即可工作
- 样式可以完全用 Tailwind 重写，保持功能不变

**Alternatives Considered**:
- 保留 Bootstrap CSS：会与 Tailwind 冲突，增加包体积
- 使用 Headless UI：需要重写所有组件，工作量大

**Implementation Notes**:
- Modal 需要 `.modal`、`.modal-dialog`、`.modal-content` 结构，但样式用 Tailwind
- Tooltip/Popover 需要 `data-bs-toggle` 属性，样式用 Tailwind 覆盖
- 保留 `bootstrap.bundle.min.js`（包含 Popper.js）

### 2. Tailwind CDN Configuration Centralization

**Decision**: 在 base.html 中定义唯一的 Tailwind 配置，所有子页面继承

**Rationale**:
- 当前配置分散在多个独立页面（login.html、admin/login.html 等）
- 集中配置便于维护和一致性
- CDN 模式下配置通过 `<script>` 标签定义

**Configuration Structure**:
```javascript
tailwind.config = {
  theme: {
    extend: {
      colors: {
        brand: { 50: '#f0f9ff', ..., 600: '#4f46e5' },
        // 从 FRONTEND_GUIDE.md 提取的颜色
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
        'shake': 'shake 0.5s ease-in-out',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        shake: { '0%, 100%': { transform: 'translateX(0)' }, '25%': { transform: 'translateX(-5px)' }, '75%': { transform: 'translateX(5px)' } },
      },
    },
  },
}
```

### 3. Glassmorphism Effects in Tailwind

**Decision**: 使用 Tailwind 内置类实现玻璃态效果

**Rationale**:
- Tailwind 3.x 原生支持 `backdrop-blur`、`bg-opacity` 等
- 无需自定义 CSS，保持纯 Tailwind 实现

**Pattern Mapping**:
```css
/* 原 CSS */
.glass-panel {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
}

/* Tailwind 等效 */
class="bg-white/70 backdrop-blur-xl border border-white/20 rounded-2xl"
```

**Browser Compatibility**:
- `backdrop-filter` 在 Safari 需要 `-webkit-` 前缀
- Tailwind CDN 自动处理前缀
- 降级方案：不支持时显示纯色背景 `bg-white/90`

### 4. Dynamic Inline Styles in JavaScript

**Decision**: 保留 JS 中的动态样式设置，仅转换静态样式

**Rationale**:
- `chat-ui.js` 中的 `.style.width`、`.style.height` 等用于运行时计算
- 这些无法用 Tailwind 类替代，因为值是动态计算的
- 静态样式（如 `display: none`）可以用 Tailwind 类

**Conversion Strategy**:
```javascript
// 保留（动态计算）
element.style.width = `${calculatedWidth}px`;
element.style.left = `${mouseX - offsetX}px`;

// 转换（静态值）
// Before: element.style.display = 'none';
// After: element.classList.add('hidden');

// Before: element.style.display = 'flex';
// After: element.classList.remove('hidden'); element.classList.add('flex');
```

### 5. Incremental Migration Strategy

**Decision**: 按组件/页面分批迁移，每批验证后再继续

**Rationale**:
- 降低风险，便于回滚
- 可以逐步验证视觉一致性
- 不影响系统正常运行

**Migration Order**:
1. **Phase 1 - 基础设施**
   - 集中 Tailwind 配置到 base.html
   - 移除子页面的重复配置

2. **Phase 2 - 核心组件**
   - 转换 style.css 中的通用样式
   - 更新 base.html 中的布局样式

3. **Phase 3 - AI 聊天组件**
   - 转换 ai_chat.css
   - 更新 chat-ui.js 中的静态样式

4. **Phase 4 - 页面模板**
   - 逐页转换内联 `<style>` 块
   - 按优先级：dashboard → grading → library → others

5. **Phase 5 - 清理**
   - 删除 style.css、ai_chat.css
   - 删除 Bootstrap CSS 文件
   - 验证所有页面

### 6. CSS Class to Tailwind Mapping Reference

**Common Patterns**:

| CSS Property | Tailwind Class |
|--------------|----------------|
| `display: flex` | `flex` |
| `display: none` | `hidden` |
| `position: fixed` | `fixed` |
| `position: absolute` | `absolute` |
| `position: relative` | `relative` |
| `width: 100%` | `w-full` |
| `height: 100vh` | `h-screen` |
| `margin: 0 auto` | `mx-auto` |
| `padding: 1rem` | `p-4` |
| `border-radius: 8px` | `rounded-lg` |
| `border-radius: 16px` | `rounded-2xl` |
| `box-shadow: ...` | `shadow-lg` / `shadow-xl` |
| `transition: all 0.3s` | `transition-all duration-300` |
| `cursor: pointer` | `cursor-pointer` |
| `overflow: hidden` | `overflow-hidden` |
| `z-index: 50` | `z-50` |

**Color Mapping** (from FRONTEND_GUIDE.md):

| Design Token | Tailwind Class |
|--------------|----------------|
| Primary (Indigo) | `indigo-500`, `indigo-600` |
| Success (Green) | `emerald-500` |
| Warning (Yellow) | `amber-500` |
| Danger (Red) | `rose-500` |
| Neutral (Slate) | `slate-50` to `slate-800` |

### 7. Files to Delete After Migration

**CSS Files (12 files)**:
- `static/css/style.css`
- `static/css/ai_chat.css`
- `static/css/bootstrap.css`
- `static/css/bootstrap.min.css`
- `static/css/bootstrap.css.map`
- `static/css/bootstrap.min.css.map`
- `static/css/bootstrap-grid.css`
- `static/css/bootstrap-grid.min.css`
- `static/css/bootstrap-reboot.css`
- `static/css/bootstrap-reboot.min.css`
- `static/css/bootstrap-utilities.css`
- `static/css/bootstrap-utilities.min.css`
- All RTL variants

**Files to Keep**:
- `static/css/all.min.css` (FontAwesome)
- `static/fonts/*` (FontAwesome fonts)
- `static/js/bootstrap.bundle.min.js` (Bootstrap JS)

## Conclusion

所有研究问题已解决，无需进一步澄清。迁移策略清晰，可以进入 Phase 1 设计阶段。
