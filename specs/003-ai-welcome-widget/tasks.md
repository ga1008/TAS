# Tasks: AI 欢迎语功能改进

**Feature**: 003-ai-welcome-widget
**Generated**: 2026-01-24
**Total Tasks**: 24

## Dependencies Graph

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational) ──────────────────────────────┐
    │                                                 │
    ├──▶ Phase 3 (US1: 定时主动问候) ◀───────────────┤
    │         │                                       │
    │         ▼                                       │
    ├──▶ Phase 4 (US2: 操作后即时反馈) ◀─────────────┤
    │         │                                       │
    │         ▼                                       │
    ├──▶ Phase 5 (US3: 手动对话交互)                 │
    │         │                                       │
    │         ▼                                       │
    ├──▶ Phase 6 (US4: 丝滑动画交互) ◀───────────────┘
    │         │
    │         ▼
    └──▶ Phase 7 (US5: 消息持久化)
              │
              ▼
        Phase 8 (Polish)
```

**Parallel Opportunities**:
- Phase 3-4 (US1, US2): 可并行开发，分别修改不同函数
- T005-T008: 后端提示词任务可并行
- T014-T016: 前端触发点绑定可并行

---

## Phase 1: Setup

> 项目准备和环境确认

- [X] T001 确认 AI 服务运行状态 `python ai_assistant.py` (端口 9011)
- [X] T002 确认数据库表存在 `data/grading_system_v2.db` (ai_welcome_messages, ai_rate_limits)

---

## Phase 2: Foundational

> 所有用户故事共享的基础设施

**Goal**: 建立"互联网老油条"人设提示词和速率限制机制

- [X] T003 更新 Few-Shot 示例库 (10+ 示例) in `services/ai_prompts.py`
- [X] T004 实现角色设定提示词模板 in `services/ai_prompts.py`
- [X] T005 [P] 添加速率限制检查函数 (60s/10s 冷却) in `blueprints/ai_welcome.py`
- [X] T006 [P] 添加回退消息池 (按时间段选择) in `services/ai_content_service.py`

---

## Phase 3: User Story 1 - 定时主动问候 (P1)

**Story Goal**: 用户停留页面 1-10 分钟后，AI 主动弹出有趣问候

**Independent Test**: 在任意页面停留 3 分钟以上，观察气泡弹出

**Acceptance Criteria**:
- 随机定时器 (1-10 分钟) 触发
- 1 分钟冷却时间
- AI 不可用时显示思考动画，无文字提示

### Implementation

- [X] T007 [US1] 实现全局随机定时器 (setTimeout + visibilitychange) in `static/js/ai-welcome.js`
- [X] T008 [US1] 实现 `scheduleNextWelcome()` 函数 (1-10分钟随机) in `static/js/ai-welcome.js`
- [X] T009 [US1] 实现 `triggerProactiveWelcome()` 函数 (调用后端 API) in `static/js/ai-welcome.js`
- [X] T010 [US1] 添加前端冷却时间检查 (localStorage 记录上次触发时间) in `static/js/ai-welcome.js`
- [X] T011 [US1] 增强 POST /api/welcome/messages 端点 (timer 触发类型) in `blueprints/ai_welcome.py`

---

## Phase 4: User Story 2 - 操作后即时反馈 (P1)

**Story Goal**: 完成关键操作后，AI 给出有趣反馈和下一步引导

**Independent Test**: 执行"生成批改核心"操作，观察操作完成后的 AI 反馈

**Acceptance Criteria**:
- 5 个核心操作触发：generate_grader, import_students, create_class, grading_complete, export_grades
- 10 秒冷却时间
- 成功/失败不同反馈

### Implementation

- [X] T012 [US2] 实现 `AIWelcome.triggerAction(operationType, details)` in `static/js/ai-welcome.js`
- [X] T013 [US2] 实现 POST /api/welcome/operation-feedback 端点 in `blueprints/ai_welcome.py`
- [X] T014 [P] [US2] 在 ai_generator.html 生成成功回调中添加触发 in `templates/ai_generator.html`
- [X] T015 [P] [US2] 在学生导入成功回调中添加触发 in `templates/student/list.html`
- [X] T016 [P] [US2] 在班级创建、批改完成、成绩导出回调中添加触发 (各相关模板)

---

## Phase 5: User Story 3 - 手动对话交互 (P2)

**Story Goal**: 用户点击浮动按钮，展开聊天窗口主动提问

**Independent Test**: 点击右下角按钮，输入"怎么批改作业"，观察 AI 回复

**Acceptance Criteria**:
- 窗口丝滑展开，输入框自动聚焦
- 消息历史使用 sessionStorage 保留 (关闭浏览器清空)
- AI 回复包含幽默调侃 + 准确操作步骤

### Implementation

- [X] T017 [US3] 实现 sessionStorage 聊天历史存取 (最多 50 条) in `static/js/ai-welcome.js`
- [X] T018 [US3] 实现 `AIWelcome.sendMessage(content)` 函数 in `static/js/ai-welcome.js`
- [X] T019 [US3] 增强 POST /api/welcome/chat 端点 (包含页面上下文) in `blueprints/ai_welcome.py`
- [X] T020 [US3] 实现聊天窗口消息渲染 (用户右侧，AI 左侧) in `static/js/ai-welcome.js`

---

## Phase 6: User Story 4 - 丝滑动画交互 (P2)

**Story Goal**: 所有弹窗、展开、收缩操作有流畅动画过渡

**Independent Test**: 反复展开/收起聊天窗口，观察动画流畅度

**Acceptance Criteria**:
- 气泡从下方滑入并缩放 (≤300ms)
- 聊天窗口缩放展开/收起 (≤300ms)
- 打字机效果 (~35ms/字)

### Implementation

- [X] T021 [US4] 优化气泡弹出动画 (cubic-bezier 弹性曲线) in `templates/components/ai_assistant_widget.html`
- [X] T022 [US4] 优化聊天窗口展开/收起动画 in `templates/components/ai_assistant_widget.html`
- [X] T023 [US4] 实现气泡高度自适应 (max-width: 320px) in `templates/components/ai_assistant_widget.html`

---

## Phase 7: User Story 5 - 消息持久化 (P3)

**Story Goal**: 生成的 AI 欢迎语保存到数据库

**Independent Test**: 触发一条欢迎语后，查询 ai_welcome_messages 表

**Acceptance Criteria**:
- 消息内容、用户ID、页面上下文、生成时间保存
- 超过 30 天的记录自动清理

### Implementation

- [X] T024 [US5] 实现 30 天数据清理函数 in `blueprints/ai_welcome.py`
- [X] T025 [US5] 在应用启动时调用清理函数 in `app.py`

---

## Phase 8: Polish & Integration

> 跨故事集成和最终验证

- [X] T026 验证所有 5 个操作触发点正常工作
- [X] T027 验证定时触发 + 操作触发 + 手动对话三种模式互不冲突
- [X] T028 验证速率限制 (60s/10s) 生效
- [X] T029 验证 AI 不可用时回退消息正���显示

---

## Implementation Strategy

### MVP Scope (建议先完成)

**Phase 1-3 (US1: 定时主动问候)**
- 完成后用户即可体验核心的"AI 主动问候"功能
- 包含基础的"老油条"人设和速率限制

### Incremental Delivery

1. **Week 1**: Phase 1-3 (Setup + Foundational + US1)
2. **Week 2**: Phase 4 (US2: 操作反馈)
3. **Week 3**: Phase 5-6 (US3: 对话 + US4: 动画优化)
4. **Week 4**: Phase 7-8 (US5: 持久化 + Polish)

---

## Summary

| Phase | User Story | Task Count | Parallel Tasks |
|-------|-----------|------------|----------------|
| 1 | Setup | 2 | 0 |
| 2 | Foundational | 4 | 2 |
| 3 | US1: 定时主动问候 | 5 | 0 |
| 4 | US2: 操作后即时反馈 | 5 | 3 |
| 5 | US3: 手动对话交互 | 4 | 0 |
| 6 | US4: 丝滑动画交互 | 3 | 0 |
| 7 | US5: 消息持久化 | 2 | 0 |
| 8 | Polish | 4 | 0 |
| **Total** | | **29** | **5** |
