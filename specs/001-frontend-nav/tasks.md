# Tasks: 前端导航架构重构

**Input**: Design documents from `/specs/001-frontend-nav/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
  ============================================================================
   IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

   The /speckit.tasks command MUST replace these with actual tasks based on:
   - User stories from spec.md (with their priorities P1, P2, P3...)
   - Feature requirements from plan.md
   - Entities from data-model.md
   - Endpoints from contracts/

   Tasks MUST be organized by user story so each story can be:
   - Implemented independently
   - Tested independently
   - Delivered as an MVP increment

   DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 创建组件目录结构 templates/components/topbar/ 和 templates/components/stats/
- [ ] T002 [P] 创建 services/stats_service.py 文件，定义 StatsService 类
- [ ] T003 [P] 创建统计 API 路由蓝图 blueprints/stats.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST complete before ANY user story can begin

- [ ] T004 实现 StatsService.get_dashboard_stats(user_id) 方法，返回班级数、学生数、批改核心数、待处理任务数
- [ ] T005 [P] 实现 StatsService.get_recent_activities(user_id) 方法，返回最近班级和批改核心
- [ ] T006 [P] 在 StatsService 添加会话缓存支持，使用 Flask session 缓存统计数据
- [ ] T007 在 blueprints/stats.py 添加 GET /api/stats/summary 路由
- [ ] T008 在 blueprints/stats.py 添加 POST /api/stats/refresh 路由
- [ ] T009 在 app.py 注册 stats 蓝图
- [ ] T010 修改 templates/base.html，添加顶栏 block 占位符 `{% block topbar %}{% endblock %}`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 仪表盘首页概览 (Priority: P1) 🎯 MVP

**Goal**: 创建新的仪表盘首页，显示统计概览、快捷操作入口、最近活动

**Independent Test**: 用户登录后访问 `/` 能看到包含 4 个统计卡片、3 个快捷操作入口、最近活动列表的仪表盘页面，而非之前的班级列表

### Implementation for User Story 1

- [ ] T011 [P] [US1] 创建 templates/components/stats/stat_card.html 统计卡片组件
- [ ] T012 [P] [US1] 创建 templates/components/stats/quick_action.html 快捷操作入口组件
- [ ] T013 [P] [US1] 创建 templates/components/stats/activity_item.html 活动条目组件
- [ ] T014 [US1] 创建 templates/components/topbar/dashboard_topbar.html 仪表盘顶栏组件（刷新按钮 + 通知中心）
- [ ] T015 [US1] 创建 templates/dashboard.html 仪表盘页面模板
  - 使用 stat_card.html 显示 4 个统计卡片（班级、学生、核心、待处理）
  - 使用 quick_action.html 显示 3 个快捷入口（新建班级、生成核心、导入学生）
  - 使用 activity_item.html 显示最近活动列表
  - 实现空状态：无数据时显示欢迎消息和突出的快捷操作入口
- [ ] T016 [US1] 修改 blueprints/main.py 的 `/` 路由，调用 StatsService 获取数据并渲染 dashboard.html
- [ ] T017 [US1] 在 dashboard.html 添加统计数据刷新按钮，点击调用 /api/stats/refresh 并更新页面
- [ ] T018 [US1] 确保仪表盘页面遵循 FRONTEND_GUIDE.md 规范（渐变背景、毛玻璃效果、Tailwind 配置）

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 批改任务管理 (Priority: P1)

**Goal**: 将原首页班级列表迁移到独立的 /tasks 页面

**Independent Test**: 用户访问 `/tasks` 能看到班级卡片列表，点击班级卡片进入批改详情页面

### Implementation for User Story 2

- [ ] T019 [P] [US2] 创建 templates/components/topbar/tasks_topbar.html 批改任务顶栏组件（新建班级按钮 + 搜索框 + 通知中心）
- [ ] T020 [US2] 创建 templates/tasks.html 批改任务列表页面
  - 复用原 templates/index.html 的班级卡片网格布局
  - 实现 SPA Router 兼容的搜索功能
  - 实现空状态引导（新建班级、生成核心）
- [ ] T021 [US2] 在 blueprints/main.py 添加 `/tasks` 路由，复用 get_classes(user_id) 逻辑并渲染 tasks.html
- [ ] T022 [US2] 在 tasks.html 添加"新建班级"按钮，点击跳转到 `/new_class`
- [ ] T023 [US2] 更新 base.html 侧边栏，添加"批改任务"菜单项链接到 `/tasks`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 规范化侧边栏菜单 (Priority: P2)

**Goal**: 按功能区域重新组织侧边栏菜单结构

**Independent Test**: 侧边栏菜单按 spec.md 结构组织，分类标题清晰，图标直观

### Implementation for User Story 3

- [ ] T024 [US3] 修改 templates/base.html 侧边栏菜单结构
  - 概览：仪表盘 (`/`)
  - 批改管理：批改任务 (`/tasks`)、新建班级 (`/new_class`)
  - AI 工具：生成核心 (`/ai_generator`)、核心列表 (`/ai_core_list`)
  - 资源管理：学生名单 (`/student/`)、文档库 (`/library/view`)、文件管理 (`/file_manager`)
  - 系统：教务系统同步 (`/jwxt/view`)、管理员后台 (modal)、退出登录 (`/logout`)
- [ ] T025 [US3] 为每个菜单项添加 FontAwesome 图标
- [ ] T026 [US3] 添加菜单分组标题（`nav-category` class）
- [ ] T027 [US3] 移除原有的多层嵌套子菜单结构，使用扁平化布局
- [ ] T028 [US3] 确保 SPA Router 正确高亮当前页面菜单项（updateActiveMenu 兼容新路由）

**Checkpoint**: All user stories 1-3 should now work independently

---

## Phase 6: User Story 4 - 上下文相关顶栏 (Priority: P2)

**Goal**: 根据页面动态显示不同的顶栏操作按钮

**Independent Test**: 不同页面显示对应的顶栏组件，操作按钮功能正常

### Implementation for User Story 4

- [ ] T029 [P] [US4] 创建 templates/components/topbar/grading_topbar.html 批改详情顶栏组件（面包屑 + 返回 + 导出 + 清空 + 删除）
- [ ] T030 [P] [US4] 创建 templates/components/topbar/ai_generator_topbar.html AI 生成页面顶栏（查看核心列表 + 通知中心）
- [ ] T031 [P] [US4] 创建 templates/components/topbar/ai_list_topbar.html 核心列表页面顶栏（生成新核心 + 搜索框）
- [ ] T032 [P] [US4] 创建 templates/components/topbar/student_list_topbar.html 学生名单页面顶栏（导入学生 + 搜索框）
- [ ] T033 [P] [US4] 创建 templates/components/topbar/library_topbar.html 文档库页面顶栏（上传文档 + 筛选器）
- [ ] T034 [US4] 修改 templates/grading.html 和 templates/student_detail.html，使用 `{% block topbar %}` 引入对应顶栏组件
- [ ] T035 [US4] 修改 templates/ai_generator.html 和 templates/ai_core_list.html，使用 `{% block topbar %}` 引入对应顶栏组件
- [ ] T036 [US4] 修改 templates/library/index.html 和 templates/student/list.html，使用 `{% block topbar %}` 引入对应顶栏组件
- [ ] T037 [US4] 创建 static/js/context_topbar.js，管理顶栏动态交互（搜索展开、通知轮询）

**Checkpoint**: All user stories 1-4 should now work independently

---

## Phase 7: User Story 5 - 面包屑导航 (Priority: P3)

**Goal**: 在深层级页面添加面包屑导航

**Independent Test**: 批改详情、学生详情页面显示面包屑导航，点击可返回上级

### Implementation for User Story 5

- [ ] T038 [P] [US5] 创建 templates/components/breadcrumb.html 面包屑组件（支持动态生成层级）
- [ ] T039 [US5] 在 templates/components/topbar/grading_topbar.html 集成面包屑组件
- [ ] T040 [US5] 修改 templates/student_detail.html，传递面包屑数据到顶栏组件
- [ ] T041 [US5] 修改 templates/ai_core_list.html 中 grader 详情链接，传递面包屑数据
- [ ] T042 [US5] 在 base.html 添加面包屑 CSS 样式（hover 效果、分隔符）

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] 添加移动端响应式样式：在 base.css 添加 `@media (max-width: 768px)` 媒体查询
- [ ] T044 [P] 实现移动端汉堡菜单按钮：在 base.html 添加汉堡按钮（移动端显示）
- [ ] T045 实现移动端侧边栏覆盖层效果：点击汉堡菜单展开侧边栏，点击遮罩层收起
- [ ] T046 [P] 更新 base.html 侧边栏添加展开/收起切换按钮
- [ ] T047 确保所有新增页面通过 FRONTEND_GUIDE.md 验证（毛玻璃、渐变背景、交互反馈）
- [ ] T048 更新 spa_router.js 的 updateActiveMenu 函数，支持新路由 `/tasks` 的高亮
- [ ] T049 测试所有页面在不同浏览器（Chrome、Firefox、Safari、Edge）的兼容性
- [ ] T050 验证成功标准 SC-001：仪表盘页面 3 秒内加载完成（使用 performance API 测试）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P1): Can start after Foundational - May integrate with US1 components but should be independently testable
  - User Story 3 (P2): Can start after Foundational - Updates base.html, may affect menu highlights
  - User Story 4 (P2): Can start after Foundational - Creates topbar components for existing pages
  - User Story 5 (P3): Can start after Foundational - Adds breadcrumbs to deep pages
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Links to `/new_class` (existing), independent of US1
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Affects base.html which all pages use
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Creates components used by existing pages
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Integrates with topbar components from US4

### Within Each User Story

- 组件创建 [P] 可以并行执行
- 组件依赖模板：stat_card/quick_action/activity_item → dashboard.html
- 路由依赖服务：StatsService 完成后才能添加路由
- 模板创建先于路由修改：dashboard.html 完成后才能修改 main.py

### Parallel Opportunities

All Setup tasks marked [P] can run in parallel.

Within User Story 1:
- T011, T012, T013 (组件创建) 可以并行
- T014 (顶栏组件) 可以与 T011-T013 并行

Within User Story 4:
- T029, T030, T031, T032, T033, T034 (顶栏组件创建) 可以并行
- T035, T036 (模板集成) 需要等待对应组件创建完成

---

## Parallel Example: User Story 1

```bash
# Launch all component creation together:
Task: "创建 templates/components/stats/stat_card.html"
Task: "创建 templates/components/stats/quick_action.html"
Task: "创建 templates/components/stats/activity_item.html"

# Dashboard topbar can run in parallel with above:
Task: "创建 templates/components/topbar/dashboard_topbar.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (仪表盘首页)
4. Complete Phase 4: User Story 2 (批改任务页面)
5. **STOP and VALIDATE**: Test both dashboard and tasks pages independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (仪表盘)
   - Developer B: User Story 2 (批改任务)
   - Developer C: User Story 3 (侧边栏) - wait for base.html availability
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (if tests were requested)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
