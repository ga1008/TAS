# Implementation Plan: AI 欢迎语功能改进

**Branch**: `003-ai-welcome-widget` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-ai-welcome-widget/spec.md`

## Summary

改进现有 AI 欢迎语系统，实现三种触发机制（定时/操作/手动）、丝滑动画交互、"互联网老油条"人设内容生成，以及消息持久化与自动清理。基于现有 `ai_welcome.py`、`ai_content_service.py`、`ai-welcome.js` 和 `ai_assistant_widget.html` 进行增强。

## Technical Context

**Language/Version**: Python 3.11 + Flask 2.x
**Primary Dependencies**: Flask, Jinja2, httpx, Tailwind CSS
**Storage**: SQLite (`data/grading_system_v2.db`) - 已有 `ai_welcome_messages`, `ai_conversations`, `ai_messages`, `ai_rate_limits` 表
**Testing**: 手动测试 + 浏览器 DevTools
**Target Platform**: Web 应用 (Windows/Linux 服务器)
**Project Type**: Web 应用（Flask 后端 + Jinja2 模板前端）
**Performance Goals**: 动画 ≤300ms, 聊天窗口响应 ≤100ms, 操作反馈 ≤2s
**Constraints**: AI 服务端口 9011, 使用 standard 模型, 欢迎语 ≤40字
**Scale/Scope**: 单用户教学场景，预计并发 <100

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **模块化解耦**: 触发逻辑在前端 JS，生成逻辑在后端服务层，职责清晰
- [x] **微服务分离**: AI 调用通过 HTTP 请求到 `ai_assistant.py` (端口 9011)
- [x] **前端设计一致性**: 使用 Tailwind CSS + 毛玻璃效果，遵循 FRONTEND_GUIDE.md
- [x] **批改器可扩展性**: 不涉及批改逻辑
- [x] **数据库迁移友好**: 使用现有表结构，新增 30 天清理逻辑
- [x] **AI 能力分层**: 使用 `standard` 能力类型，有降级到回退消息的策略
- [x] **AI 内容生成与缓存**: 使用 `ai_welcome_messages` 表缓存，有 TTL 过期机制
- [x] **前端 AI 内容展示**: 打字机效果逐字显示，气泡高度自适应
- [x] **AI 提示工程**: 提示词包含 Few-Shot 示例，明确输出格式
- [x] **个性化AI交互**: 包含用户名、时间、统计数据、最近操作等上下文

## Project Structure

### Documentation (this feature)

```text
specs/003-ai-welcome-widget/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
autoCorrecting/
├── blueprints/
│   └── ai_welcome.py              # [MODIFY] 添加操作反馈 API, 30天清理逻辑
├── services/
│   ├── ai_content_service.py      # [MODIFY] 增强提示词，添加"互联网老油条"人设
│   ├── ai_prompts.py              # [MODIFY] 更新 Few-Shot 示例
│   └── ai_conversation_service.py # [EXISTING] 对话服务
├── templates/
│   └── components/
│       └── ai_assistant_widget.html  # [MODIFY] 优化动画，自适应高度
├── static/js/
│   └── ai-welcome.js              # [MODIFY] 添加定时器、操作触发、sessionStorage
└── database.py                    # [EXISTING] 已有所需表结构
```

**Structure Decision**: 使用现有 Flask Web 应用结构，不新增模块，仅增强现有文件。

## Complexity Tracking

> 无宪法违规，无需记录。
