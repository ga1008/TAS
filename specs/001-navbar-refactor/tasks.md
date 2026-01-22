# Tasks: 侧边栏与顶栏导航系统重构

**Input**: Design documents from `/specs/001-navbar-refactor/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, quickstart.md

**Tests**: 无自动化测试，手动验证即可（spec.md未要求自动化测试）。

**Organization**: 任务按用户故事组织，支持独立实施和验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 任务所属用户故事 (US1, US2, US3)
- 描述中包含精确文件路径

---

## Phase 1: Setup (基础准备)

**Purpose**: 确认项目状态，备份关键文件

- [x] T001 确认当前分支为 `001-navbar-refactor`
- [x] T002 [P] 备份 `static/js/spa_router.js` (复制为 spa_router.js.bak)
- [x] T003 [P] 备份 `templates/base.html` (复制为 base.html.bak)

---

## Phase 2: Foundational (阻塞性基础任务)

**Purpose**: 核心导航修复 - 必须在所有用户故事之前完成

**⚠️ CRITICAL**: 此阶段完成前，任何用户故事任务都无法开始

- [x] T004 修改 `static/js/spa_router.js` 中 `shouldIntercept()` 函数返回 `false`，禁用 SPA 拦截
- [x] T005 验证禁用 SPA 后侧边栏导航为全页刷新（点击任意菜单项，观察浏览器地址栏刷新）

**Checkpoint**: SPA 路由已禁用，导航恢复全页刷新模式

---

## Phase 3: User Story 1 - 菜单导航功能正常 (Priority: P1) 🎯 MVP

**Goal**: 确保通过侧边菜单导航到任意页面后，该页面的所有JavaScript功能完整可用

**Independent Test**: 从首页通过侧边菜单依次访问所有功能页，验证每个页面的核心功能是否可用

### Implementation for User Story 1

- [x] T006 [US1] 在 `templates/base.html` 侧边栏为首页链接添加 Jinja2 active 判断: `{% if request.path == '/' %}active{% endif %}`
- [x] T007 [P] [US1] 在 `templates/base.html` 为新建任务链接添加 active 判断: `{% if request.path == '/new_class' %}active{% endif %}`
- [x] T008 [P] [US1] 在 `templates/base.html` 为任务管理链接添加 active 判断: `{% if request.path.startswith('/tasks') %}active{% endif %}`
- [x] T009 [P] [US1] 在 `templates/base.html` 为生成核心链接添加 active 判断: `{% if request.path.startswith('/ai_generator') %}active{% endif %}`
- [x] T010 [P] [US1] 在 `templates/base.html` 为核心列表链接添加 active 判断: `{% if request.path.startswith('/ai_core_list') %}active{% endif %}`
- [x] T011 [P] [US1] 在 `templates/base.html` 为班级学生链接添加 active 判断: `{% if request.path.startswith('/student') %}active{% endif %}`
- [x] T012 [P] [US1] 在 `templates/base.html` 为教学文档链接添加 active 判断: `{% if request.path.startswith('/library') %}active{% endif %}`
- [x] T013 [P] [US1] 在 `templates/base.html` 为文档解析链接添加 active 判断: `{% if request.path.startswith('/file_manager') %}active{% endif %}`
- [x] T014 [P] [US1] 在 `templates/base.html` 为教务系统链接添加 active 判断: `{% if request.path.startswith('/jwxt') %}active{% endif %}`
- [ ] T015 [US1] 手动验证：从首页依次访问每个侧边菜单项，确认：
  - 页面完整加载
  - DevTools Console 无 JS 错误
  - 核心功能可用（按钮点击、表单提交等）
- [ ] T016 [US1] 手动验证：使用浏览器后退/前进按钮，确认页面正确显示且功能完整

**Checkpoint**: User Story 1 完成 - 菜单导航功能正常，页面功能100%可用

---

## Phase 4: User Story 2 - 顶栏导航与快捷操作 (Priority: P2)

**Goal**: 顶栏根据当前页面动态显示相关的快捷操作按钮

**Independent Test**: 访问不同功能页面，验证顶栏按钮是否与当前页面功能匹配

### 创建 Topbar 组件

- [x] T017 [P] [US2] 创建 `templates/components/topbar/ai_generator_topbar.html`，包含：页面标题、"文档解析管理"链接、"核心列表"链接、通知中心
- [x] T018 [P] [US2] 创建 `templates/components/topbar/ai_core_list_topbar.html`，包含：页面标题、"生成新核心"链接、"回收站"按钮、通知中心
- [x] T019 [P] [US2] 创建 `templates/components/topbar/student_list_topbar.html`，包含：页面标题、"创建新班级"按钮、通知中心
- [x] T020 [P] [US2] 创建 `templates/components/topbar/library_topbar.html`，包含：页面标题、"上传文档"按钮、通知中心
- [x] T021 [P] [US2] 创建 `templates/components/topbar/file_manager_topbar.html`，包含：页面标题、"返回文档库"链接、通知中心
- [x] T022 [P] [US2] 创建 `templates/components/topbar/jwxt_topbar.html`，包含：页面标题、"同步数据"按钮（条件显示）、通知中心

### 更新页面模板使用 Topbar

- [x] T023 [US2] 修改 `templates/ai_generator.html`：添加 `{% block topbar %}{% include 'components/topbar/ai_generator_topbar.html' %}{% endblock %}`，移除页面内重复操作栏
- [x] T024 [US2] 修改 `templates/ai_core_list.html`：添加 `{% block topbar %}{% include 'components/topbar/ai_core_list_topbar.html' %}{% endblock %}`，移除页面内重复操作栏
- [x] T025 [US2] 修改 `templates/student/list.html`：添加 `{% block topbar %}{% include 'components/topbar/student_list_topbar.html' %}{% endblock %}`，移除页面内重复操作栏
- [x] T026 [US2] 修改 `templates/library/index.html`：添加 `{% block topbar %}{% include 'components/topbar/library_topbar.html' %}{% endblock %}`，移除页面内重复操作栏
- [x] T027 [US2] 修改 `templates/file_manager.html`：添加 `{% block topbar %}{% include 'components/topbar/file_manager_topbar.html' %}{% endblock %}`，移除页面内重复操作栏
- [x] T028 [US2] 修改 `templates/jwxt_connect.html`：添加 `{% block topbar %}{% include 'components/topbar/jwxt_topbar.html' %}{% endblock %}`
- [ ] T029 [US2] 手动验证：访问每个功能页，确认顶栏按钮与页面功能匹配
- [ ] T030 [US2] 手动验证：点击顶栏"返回"和"首页"按钮，确认导航正常

**Checkpoint**: User Story 2 完成 - 顶栏按钮与页面功能匹配

---

## Phase 5: User Story 3 - 视觉一致性与交互反馈 (Priority: P3)

**Goal**: 提供流畅的过渡动画和清晰的交互反馈

**Independent Test**: 视觉检查侧边栏和顶栏在不同页面的呈现效果

### Implementation for User Story 3

- [x] T031 [US3] 在 `templates/base.html` 添加加载指示器 HTML 元素: `<div class="page-loading-bar" id="page-loading-bar"></div>`
- [x] T032 [US3] 在 `templates/base.html` 添加加载指示器 CSS 样式 (NProgress 风格，顶部进度条)
- [x] T033 [US3] 在 `templates/base.html` 添加 JS 监听 `beforeunload` 事件显示加载指示器
- [ ] T034 [US3] 手动验证：点击菜单后加载指示器立即显示，页面加载完成后消失
- [ ] T035 [US3] 手动验证：侧边栏当前页面菜单项高亮正确
- [ ] T036 [US3] 手动验证：所有顶栏按钮使用 `.btn-glass` 样式
- [ ] T037 [US3] 手动验证：悬停菜单项/按钮时有平滑过渡动画

**Checkpoint**: User Story 3 完成 - 视觉一致性和交互反馈达标

---

## Phase 6: Polish & 验收

**Purpose**: 最终验收和清理

- [ ] T038 完整回归测试：从首页访问所有功能页，验证所有成功标准
- [x] T039 清理备份文件：删除 `spa_router.js.bak` 和 `base.html.bak`
- [x] T040 更新 `specs/001-navbar-refactor/quickstart.md` 标记已完成的任务

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 - 可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - 阻塞所有用户故事
- **User Story 1 (Phase 3)**: 依赖 Foundational 完成
- **User Story 2 (Phase 4)**: 依赖 Foundational 完成 (可与 US1 并行)
- **User Story 3 (Phase 5)**: 依赖 Foundational 完成 (可与 US1/US2 并行)
- **Polish (Phase 6)**: 依赖所有用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: 独立可测试 - 核心导航功能
- **User Story 2 (P2)**: 独立可测试 - 顶栏按钮 (可与 US1 并行，不冲突的文件)
- **User Story 3 (P3)**: 独立可测试 - 视觉反馈 (可与 US1/US2 并行，修改 base.html 不同部分)

### Within Each User Story

- T006-T014: 服务端菜单激活判断（可并行，修改 base.html 不同行）
- T017-T022: 创建 topbar 组件（可并行，不同文件）
- T023-T028: 更新页面模板（顺序执行，避免冲突）

### Parallel Opportunities

- T002, T003 可并行执行
- T007-T014 可并行执行（同文件不同位置，需谨慎）
- T017-T022 可并行执行（不同文件）

---

## Parallel Example: User Story 2 Topbar Components

```bash
# 可同时创建所有 topbar 组件（不同文件）：
Task: "创建 ai_generator_topbar.html"
Task: "创建 ai_core_list_topbar.html"
Task: "创建 student_list_topbar.html"
Task: "创建 library_topbar.html"
Task: "创建 file_manager_topbar.html"
Task: "创建 jwxt_topbar.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (备份文件)
2. Complete Phase 2: Foundational (禁用 SPA 路由) - **CRITICAL**
3. Complete Phase 3: User Story 1 (服务端菜单激活)
4. **STOP and VALIDATE**: 测试导航功能，确认无 JS 错误
5. 可交付 MVP：导航功能正常

### Incremental Delivery

1. Setup + Foundational → 基础就绪
2. Add User Story 1 → 测试 → 交付 (MVP: 导航功能修复)
3. Add User Story 2 → 测试 → 交付 (顶栏按钮统一)
4. Add User Story 3 → 测试 → 交付 (视觉一致性)

### Single Developer Strategy

推荐顺序：Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

---

## Summary

- **Total Tasks**: 40
- **User Story 1 (P1)**: 11 tasks (T006-T016)
- **User Story 2 (P2)**: 14 tasks (T017-T030)
- **User Story 3 (P3)**: 7 tasks (T031-T037)
- **Setup/Foundational**: 5 tasks (T001-T005)
- **Polish**: 3 tasks (T038-T040)
- **Parallel Opportunities**: 16 tasks marked [P]
- **MVP Scope**: Phase 1-3 (T001-T016, 导航功能正常)

---

## Notes

- [P] tasks = 不同文件，无依赖，可并行
- [Story] label = 关联到特定用户故事，便于追踪
- 每个用户故事可独立完成和测试
- 手动验证代替自动化测试（spec.md 未要求）
- 完成一个阶段后再进入下一阶段
- 遇到问题可回滚（保留了备份文件）
