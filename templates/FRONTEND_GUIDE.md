# AI 辅助教学系统 - 前端设计与交互规范 (Design System)

## 1. 核心设计理念 (Core Philosophy)

本系统采用 **"新拟态 (Neumorphism) + 毛玻璃 (Glassmorphism)"** 的混合设计风格。

* **视觉关键词**：通透、现代、柔和、层次感、微动效。
* **核心色彩**：以靛蓝 (Indigo) 为主色调，搭配板岩灰 (Slate) 为中性色，背景使用柔和的径向渐变。
* **交互原则**：所有的操作都应有视觉反馈（呼吸、位移、光晕），加载过程必须有细腻的动画过渡。

---

## 2. Tailwind CSS 配置 (Configuration)

在所有新页面的 `<script>` 配置中，必须包含以下自定义扩展，以保证动效和色彩的一致性。

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                brand: { 50: '#eff6ff', 100: '#dbeafe', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8' }
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-out forwards',
                'slide-up': 'slideUp 0.4s ease-out forwards',
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'shake': 'shake 0.5s ease-in-out',
            },
            keyframes: {
                fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
                slideUp: { '0%': { opacity: '0', transform: 'translateY(20px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
                shake: {
                    '0%, 100%': { transform: 'translateX(0)' },
                    '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-4px)' },
                    '20%, 40%, 60%, 80%': { transform: 'translateX(4px)' },
                }
            }
        }
    }
}

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

## 8. 示例模板 (Example Snippet)

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