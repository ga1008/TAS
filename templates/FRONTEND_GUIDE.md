# AI 辅助教学系统 - 前端设计与交互规范 (Design System)

## 1. 核心设计理念 (Core Philosophy)

本系统采用 **"新拟态 (Neumorphism) + 毛玻璃 (Glassmorphism)"** 的混合设计风格。

* **视觉关键词**：通透、现代、柔和、层次感、微动效。
* **核心色彩**：以靛蓝 (Indigo) 为主色调，搭配板岩灰 (Slate) 为中性色，背景使用柔和的径向渐变。
* **交互原则**：所有的操作都应有视觉反馈（呼吸、位移、光晕），加载过程必须有细腻的动画过渡。

---

## 2. Tailwind CSS 配置 (Configuration)

本系统使用 **Tailwind CSS CDN 模式**，统一配置定义在 `templates/base.html` 中。所有继承 base.html 的页面自动获得此配置。

**独立页面**（如 `login.html`, `admin/login.html`, `student_detail.html`, `grader_detail.html`, `export.html`）需要在各自的 `<script>` 中包含相同的配置。

### 完整配置

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                brand: { 50: '#eff6ff', 100: '#dbeafe', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8' },
                sky: { 50: '#f0f9ff', 100: '#e0f2fe', 500: '#0ea5e9', 600: '#0284c7' },
                slate: { 50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0', 300: '#cbd5e1', 400: '#94a3b8', 500: '#64748b', 600: '#475569', 700: '#334155', 800: '#1e293b', 900: '#0f172a' },
                indigo: { 50: '#eef2ff', 100: '#e0e7ff', 200: '#c7d2fe', 400: '#818cf8', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' },
                emerald: { 50: '#ecfdf5', 100: '#d1fae5', 500: '#10b981', 600: '#059669' },
                rose: { 50: '#fff1f2', 100: '#ffe4e6', 400: '#fb7185', 500: '#f43f5e', 600: '#e11d48' },
                amber: { 50: '#fffbeb', 100: '#fef3c7', 400: '#fbbf24', 500: '#f59e0b', 900: '#78350f' },
                purple: { 50: '#faf5ff', 100: '#f3e8ff', 400: '#c084fc', 500: '#a855f7', 600: '#9333ea' }
            },
            boxShadow: {
                'soft': '0 10px 40px -10px rgba(0, 0, 0, 0.08)',
                'glow': '0 0 20px rgba(99, 102, 241, 0.15)'
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-out forwards',
                'fade-in-up': 'fadeInUp 0.5s ease-out forwards',
                'slide-in': 'slideIn 0.3s ease-out',
                'slide-up': 'slideUp 0.4s ease-out forwards',
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'shake': 'shake 0.5s ease-in-out'
            },
            keyframes: {
                fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
                fadeInUp: { '0%': { opacity: '0', transform: 'translateY(10px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
                slideIn: { '0%': { transform: 'translateX(-10px)', opacity: '0' }, '100%': { transform: 'translateX(0)', opacity: '1' } },
                slideUp: { '0%': { opacity: '0', transform: 'translateY(20px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
                shake: {
                    '0%, 100%': { transform: 'translateX(0)' },
                    '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-4px)' },
                    '20%, 40%, 60%, 80%': { transform: 'translateX(4px)' }
                }
            }
        }
    }
}
```

### 补充样式 (Supplementary CSS)

复杂效果（如毛玻璃、自定义滚动条、特殊动画）使用 `<style>` 块定义，作为 Tailwind 的补充：

```css
/* 毛玻璃面板 */
.glass-panel {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.5);
}

/* 自定义滚动条 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
```

---

## 3. 布局与背景 (Layout & Background)

### 全局背景

页面 `body` **不使用纯白背景**，必须使用径向渐变和装饰性光球，营造空间感。

* **Body 类名**: `bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100 via-slate-50 to-white min-h-screen font-sans text-slate-800`
* **装饰光球 (Orbs)**: 在 `main` 容器内绝对定位，使用混合模式 (`mix-blend-multiply`)。

```html
<div class="absolute top-10 -left-10 w-64 h-64 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-slow"></div>
<div class="absolute bottom-10 -right-10 w-64 h-64 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-slow" style="animation-delay: 1s;"></div>

```

### 容器面板 (Glass Panel)

所有主要内容区域（Card, Panel, Modal）都应使用“毛玻璃”效果，而不是纯白背景。

* **CSS 类**: `.glass-panel`
* **样式定义**:

```css
.glass-panel {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.5);
}

```

* **圆角与阴影**: 通常搭配 `rounded-3xl` 和 `shadow-xl`。

---

## 4. 组件规范 (Components)

### 4.1 输入框 (Inputs) - 沉浸式设计

不要使用默认的灰色边框输入框。输入框应像是“镶嵌”在玻璃上的。

* **普通输入框**:
* 背景半透明 (`bg-white/50`)，聚焦时变白 (`bg-white/90`)。
* 无边框或极细透明边框，聚焦时显示柔和光环 (`ring`)。
* **代码参考**:


```html
<input type="text" class="w-full px-4 py-2.5 rounded-xl border-0 bg-white/50 focus:bg-white focus:ring-2 focus:ring-indigo-100 transition-all outline-none text-sm font-bold text-slate-700 placeholder:font-normal placeholder:text-slate-300">

```


* **大文本域 (Textarea)**:
* 使用内阴影 (`shadow-inner`) 营造凹陷感。
* 类名: `bg-white/60 shadow-inner ring-1 ring-slate-100`。



### 4.2 按钮 (Buttons) - 强调与微交互

主操作按钮必须显眼、有质感，且包含鼠标悬停反馈。

* **主按钮 (Primary)**:
* **背景**: 靛蓝渐变 (`bg-gradient-to-r from-indigo-600 to-blue-600`)。
* **阴影**: 彩色投影 (`shadow-lg shadow-indigo-300/50`)。
* **悬停效果**: 轻微上浮 (`hover:-translate-y-0.5`) + 阴影加深。
* **代码参考**:


```html
<button class="bg-gradient-to-r from-indigo-600 to-blue-600 text-white px-8 py-3 rounded-xl font-bold shadow-lg shadow-indigo-300/50 hover:shadow-indigo-400/60 hover:-translate-y-0.5 transition-all duration-300 flex items-center gap-2">
    <i class="fas fa-check"></i> <span>提交</span>
</button>

```


* **次级按钮 (Secondary)**:
* 透明或浅色背景，悬停时加深。
* 类名: `text-slate-500 hover:bg-slate-100/80 font-bold`。



### 4.3 表格 (Data Tables) - 悬浮卡片式

不要使用传统的网格线表格。每一行数据应该像一个悬浮的条目。

* **表头**: 固定，背景带模糊 (`backdrop-blur`)，字体小且颜色浅 (`text-xs text-slate-400 uppercase`)。
* **数据行**:
* 鼠标悬停时高亮 (`hover:bg-indigo-50/50`)。
* 圆角处理：第一列左圆角，最后一列右圆角。


* **重要数据**（如学号、ID）：使用等宽字体 (`font-mono`) 加粗。
* **缺失/错误数据**：使用 `bg-rose-100 text-rose-600` 徽章样式。

---

## 5. 交互与反馈 (Interaction & Feedback)

### 5.1 加载状态 (Loading States)

**严禁**让用户对着静止的屏幕等待。

1. **全屏加载 (Overlay)**:
* 用于文件解析、AI 生成等长耗时操作。
* 背景: `bg-white/60 backdrop-blur-sm`。
* 元素: 旋转光环 + 脉冲文字 (`animate-pulse`) + 图标。


2. **按钮加载**:
* 点击后立即禁用按钮。
* 替换文字为 `<i class="fas fa-circle-notch fa-spin"></i> 处理中...`。
* 降低透明度 `opacity-75`，鼠标样式改为 `cursor-not-allowed`。



### 5.2 步骤切换 (Transitions)

页面内的状态切换（如从“上传”变“预览”）必须有动画。

* **旧元素**: 上移并淡出 (`opacity-0 -translate-y-4`)。
* **新元素**: 下移进入或淡入 (`animate-fade-in` 或 `animate-slide-up`)。

### 5.3 错误提示

* **震动反馈**: 当校验失败时，让面板左右晃动。
* JS 调用: `panel.classList.add('animate-[shake_0.5s_ease-in-out]')`。

---

## 6. 排版与图标 (Typography & Icons)

* **字体**: 使用系统无衬线字体 (`font-sans`)，强调层级。
* *标题*: `font-bold text-slate-800`。
* *标签*: `text-xs font-bold text-slate-400 uppercase tracking-wider` (这种样式能显著提升高级感)。
* *正文*: `text-sm text-slate-600`。


* **图标**: 统一使用 **FontAwesome 6** (`<i class="fas fa-..."></i>`)。
* 图标通常搭配圆形背景容器，例如 `w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center`。



---

## 7. 导航系统 (Navigation System)

### 7.1 侧边栏 (Sidebar)

采用 **固定左侧 + 高斯模糊** 的设计，作为系统的核心导航区。

* **容器样式**:
* 固定定位，高度 100vh。
* 背景使用高透玻璃 (`bg-white/85`) + 高度模糊 (`backdrop-filter: blur(12px)`)。
* 右侧添加极细的白色边框 (`border-r border-white/50`) 以区分内容区。
* 添加轻微右侧阴影 (`shadow-[4px_0_24px_rgba(0,0,0,0.02)]`)。



### 7.2 顶部栏 (Topbar)

用于显示当前页面标题、面包屑及全局快捷操作（如返回）。

* **容器样式**:
* 固定顶部（位于 Sidebar 右侧），高度通常为 `64px`。
* 背景比侧边栏更透 (`bg-white/60`)。
* 底部边框 (`border-b border-white/50`)。



### 7.3 菜单项 (Menu Items)

菜单项不仅仅是文字，必须是可交互的“胶囊”形态。

* **默认状态 (Inactive)**:
* 文字颜色: `text-slate-500`。
* 背景: 透明。
* 交互: 悬停时背景变浅白 (`hover:bg-white/60`)，文字变深 (`hover:text-indigo-600`)，图标轻微位移。


* **激活状态 (Active)**:
* 视觉重心：必须一眼识别。
* 背景: 浅靛蓝 (`bg-indigo-50`)。
* 文字/图标: 靛蓝主色 (`text-indigo-600`)，加粗 (`font-bold`)。
* 装饰: 添加内描边 (`ring-1 ring-indigo-100`) 和轻微阴影 (`shadow-sm`)。


* **分类标题 (Category Label)**:
* 使用规范中的标签样式：`text-[10px] font-bold text-slate-400 uppercase tracking-wider px-4 mt-6 mb-2`。


* **代码示例**:

```html
<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-xl bg-indigo-50 text-indigo-600 font-bold ring-1 ring-indigo-100 shadow-sm transition-all">
    <i class="fas fa-home w-5 text-center"></i>
    <span>仪表盘</span>
</a>

<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-500 hover:bg-white/60 hover:text-indigo-600 transition-all group">
    <i class="fas fa-cog w-5 text-center group-hover:rotate-90 transition-transform"></i>
    <span>系统设置</span>
</a>

```

---

## 8. 微交互动画规范 (Micro-interaction Animations)

本系统强调**每个可交互元素都必须有视觉反馈**。以下是标准化的动画过渡类，应在页面中复用。

### 8.1 核心缓动函数

所有动画统一使用 Material Design 推荐的缓动曲线：

```css
/* 标准缓动 - 用于大多数过渡 */
transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);

/* 快速响应 - 用于微小变化 */
transition: all 0.2s ease;

/* 柔和弹性 - 用于强调效果 */
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

### 8.2 标准动画类库

以下 CSS 类应在需要时复制到页面的 `<style>` 块中：

```css
/* 玻璃面板悬浮效果 */
.glass-panel {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    transition: box-shadow 0.3s ease, transform 0.3s ease;
}
.glass-panel:hover {
    box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.1);
}

/* 玻璃输入框 - 悬浮上浮 + 聚焦光环 */
.glass-input {
    background: rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(10px);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.glass-input:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.glass-input:focus {
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
    border-color: #818cf8;
}

/* 步骤徽章 - 缩放旋转 */
.step-badge {
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
}
.step-badge:hover {
    transform: scale(1.1) rotate(-3deg);
}

/* 操作链接 - 上浮 + 阴影 + 按压反馈 */
.action-link {
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.action-link:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}
.action-link:active {
    transform: translateY(0) scale(0.98);
}

/* 下拉菜单展开动画 */
.dropdown-menu {
    animation: dropdownSlide 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes dropdownSlide {
    from { opacity: 0; transform: translateY(-8px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

/* 列表选项 - 水平滑动 */
.option-item {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.option-item:hover {
    transform: translateX(4px);
}
.option-item:active {
    transform: translateX(2px) scale(0.99);
}

/* 表单输入框聚焦放大 */
.form-input {
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.form-input:focus {
    transform: scale(1.01);
}

/* 信息卡片入场动画 */
.info-card {
    animation: infoSlide 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes infoSlide {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* 下拉箭头旋转 */
.chevron-icon {
    transition: transform 0.25s ease;
}
.dropdown-open .chevron-icon {
    transform: rotate(180deg);
}

/* 确认面板悬浮 - 带色彩阴影 */
.confirm-panel {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.confirm-panel:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 40px -15px rgba(16, 185, 129, 0.2);
}

/* 标签徽章缩放 */
.tag-badge {
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 700;
    text-transform: uppercase;
    transition: transform 0.2s ease;
}
.tag-badge:hover {
    transform: scale(1.05);
}

/* 自定义滚动条 (带悬浮效果) */
.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
    transition: background 0.2s ease;
}
.custom-scroll::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
```

### 8.3 动画时长指南

| 交互类型 | 推荐时长 | 说明 |
|---------|---------|------|
| 悬浮反馈 | 0.2s | 按钮、链接、图标 |
| 面板/卡片 | 0.3s | 大面积元素的悬浮效果 |
| 入场动画 | 0.4s | 新元素出现时 |
| 下拉展开 | 0.2s | 快速响应用户操作 |
| 图标变换 | 0.25s | 箭头旋转、图标切换 |

---

## 9. 步骤式表单布局 (Step-based Form Layout)

多步骤表单应采用**数字徽章 + 连接线**的设计，清晰展示流程。

### 9.1 步骤连接线

```css
.step-line {
    position: absolute;
    left: 19px;  /* 对齐徽章中心 */
    top: 35px;
    bottom: -20px;
    width: 2px;
    background: #e2e8f0;
    z-index: 0;
    transition: background 0.3s ease;
}
.step-item:last-child .step-line { display: none; }
.step-item:hover .step-line { background: #c7d2fe; }  /* 悬浮时高亮 */
```

### 9.2 步骤徽章

```html
<div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center text-sm font-bold shadow-lg shadow-indigo-200 step-badge cursor-default">
    1
</div>
```

* **颜色区分**: 不同步骤使用不同主色（如 indigo → sky → emerald）
* **阴影跟随**: 使用 `shadow-{color}-200` 让阴影呼应徽章颜色

### 9.3 完整步骤项结构

```html
<div class="relative z-20 step-item">
    <div class="step-line"></div>
    <div class="flex justify-between items-center mb-3 relative z-10">
        <label class="text-sm font-bold text-slate-800 flex items-center gap-3">
            <div class="step-badge ...">1</div>
            步骤标题
        </label>
        <a href="#" class="action-link ...">
            <i class="fas fa-plus"></i> 辅助操作
        </a>
    </div>
    <div class="ml-13 relative">
        <!-- 步骤内容 -->
    </div>
</div>
```

---

## 10. 下拉选择器组件 (Dropdown Selector)

自定义下拉选择器采用**玻璃输入框触发器 + 浮动面板**的设计。

### 10.1 组件结构

```html
<div class="relative" id="dropdown-container">
    <input type="hidden" name="field" id="field-input" required>

    <!-- 触发器 -->
    <div class="glass-input w-full px-4 py-4 rounded-xl cursor-pointer flex items-center justify-between group"
         onclick="toggleDropdown('dropdown-menu')" id="dropdown-trigger">
        <span id="display" class="text-slate-400 font-medium text-sm group-hover:text-indigo-500 transition-colors">
            点击选择...
        </span>
        <i class="fas fa-chevron-down text-slate-300 text-xs group-hover:text-indigo-400 chevron-icon"></i>
    </div>

    <!-- 下拉面板 -->
    <div id="dropdown-menu" class="hidden absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-2xl border border-slate-100 z-50 overflow-hidden dropdown-menu transform origin-top">
        <!-- 搜索栏 (可选) -->
        <div class="p-3 border-b border-slate-50 bg-slate-50/80 backdrop-blur-sm sticky top-0 z-10">
            <div class="relative">
                <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
                <input type="text" placeholder="搜索..."
                       class="w-full bg-white border border-slate-200 text-xs pl-8 pr-3 py-2.5 rounded-lg outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all">
            </div>
        </div>

        <!-- 选项列表 -->
        <div class="max-h-[320px] overflow-y-auto custom-scroll p-2 space-y-1">
            <div class="option-item p-3 hover:bg-indigo-50 rounded-xl cursor-pointer border border-transparent hover:border-indigo-100 group/item">
                <!-- 选项内容 -->
            </div>
        </div>
    </div>
</div>
```

### 10.2 JavaScript 控制逻辑

```javascript
function toggleDropdown(menuId) {
    const menu = document.getElementById(menuId);
    const isHidden = menu.classList.contains('hidden');

    // 关闭所有其他下拉
    document.querySelectorAll('[id$="-menu"]').forEach(el => {
        el.classList.add('hidden');
        const triggerId = el.id.replace('-menu', '-trigger');
        const trigger = document.getElementById(triggerId);
        if (trigger) trigger.classList.remove('dropdown-open');
    });

    const triggerId = menuId.replace('-menu', '-trigger');
    const trigger = document.getElementById(triggerId);

    if (isHidden) {
        menu.classList.remove('hidden');
        if (trigger) trigger.classList.add('dropdown-open');
    }
}

// 点击外部关闭
document.addEventListener('click', function(e) {
    if (!e.target.closest('#dropdown-container')) {
        document.querySelectorAll('[id$="-menu"]').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('[id$="-trigger"]').forEach(el => el.classList.remove('dropdown-open'));
    }
});
```

### 10.3 选项卡片设计

每个选项应包含：图标 + 标题 + 标签徽章 + 悬浮动画

```html
<div class="option-item p-3 hover:bg-indigo-50 rounded-xl cursor-pointer border border-transparent hover:border-indigo-100 group/item">
    <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-bold shadow-sm group-hover/item:scale-110 transition-transform">
            <i class="fas fa-code"></i>
        </div>
        <div>
            <h4 class="text-sm font-bold text-slate-700 group-hover/item:text-indigo-700 transition-colors">选项标题</h4>
            <div class="flex items-center gap-2 mt-1.5">
                <span class="tag-badge bg-slate-100 text-slate-500">分类</span>
                <span class="tag-badge bg-blue-50 text-blue-500 border border-blue-100">状态</span>
            </div>
        </div>
    </div>
</div>
```

---

## 11. 双栏确认布局 (Two-column Confirm Layout)

适用于"配置 + 确认"类页面，如新建任务、提交表单等。

### 11.1 布局结构

```html
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
    <!-- 左侧配置区 (2/3 宽度) -->
    <div class="lg:col-span-2">
        <div class="glass-panel rounded-2xl shadow-sm p-8">
            <!-- 配置表单 -->
        </div>
    </div>

    <!-- 右侧确认区 (1/3 宽度, 粘性定位) -->
    <div class="lg:col-span-1 h-full">
        <div class="glass-panel confirm-panel p-8 rounded-2xl shadow-lg border-t-4 border-emerald-500 sticky top-24 flex flex-col">
            <!-- 头部 -->
            <div class="flex items-center gap-3 mb-8 pb-4 border-b border-slate-100">
                <div class="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center text-lg">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div>
                    <h3 class="font-bold text-slate-800">信息确认</h3>
                    <p class="text-[10px] text-slate-400 uppercase tracking-wider">Confirm & Launch</p>
                </div>
            </div>

            <!-- 内容区 -->
            <div class="space-y-6 flex-1">
                <!-- 只读/确认字段 -->
            </div>

            <!-- 提交按钮 -->
            <div class="mt-8 pt-6 border-t border-slate-100">
                <button type="submit" class="w-full bg-gradient-to-r from-emerald-500 to-teal-600 text-white py-4 rounded-xl font-bold shadow-lg shadow-emerald-200 hover:shadow-xl hover:shadow-emerald-300 hover:-translate-y-0.5 transition-all duration-300 flex items-center justify-center gap-2 active:scale-95 group">
                    <span class="group-hover:scale-110 transition-transform"><i class="fas fa-rocket"></i></span>
                    <span>立即提交</span>
                </button>
            </div>
        </div>
    </div>
</div>
```

### 11.2 设计要点

* **确认面板粘性定位**: `sticky top-24` 保持可见
* **顶部色带**: `border-t-4 border-emerald-500` 突出重要性
* **悬浮效果**: 使用 `.confirm-panel` 类添加上浮 + 彩色阴影
* **按钮动效**: 包含图标放大 (`group-hover:scale-110`) 和按压反馈 (`active:scale-95`)

---

## 12. 示例模板 (Example Snippet)

当需要生成一个“卡片信息展示”组件时，请参照以下结构：

```html
<div class="glass-panel p-6 rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group relative overflow-hidden">
    
    <div class="absolute top-0 right-0 w-24 h-24 bg-indigo-50 rounded-full -mr-10 -mt-10 opacity-50 group-hover:scale-150 transition-transform duration-500"></div>

    <div class="relative z-10">
        <div class="flex items-center gap-4 mb-4">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 text-white flex items-center justify-center shadow-lg shadow-indigo-200">
                <i class="fas fa-cube text-xl"></i>
            </div>
            <div>
                <h3 class="font-bold text-lg text-slate-800">模块标题</h3>
                <p class="text-xs text-slate-400 font-medium uppercase">Subtitle Info</p>
            </div>
        </div>

        <div class="space-y-3">
            <div class="flex justify-between text-sm border-b border-slate-100/50 pb-2">
                <span class="text-slate-500">数据指标</span>
                <span class="font-mono font-bold text-indigo-600">85%</span>
            </div>
        </div>
    </div>
</div>

```