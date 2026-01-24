# Implementation Plan: Fix AI Welcome Message Display Bug

**Branch**: `001-fix-ai-welcome` | **Date**: 2025-01-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-fix-ai-welcome/spec.md`

## Summary

Fix a session key mismatch bug preventing the AI welcome assistant floating button and popup from displaying. The auth system stores `session['user']` but the template checks `session.get('user_id')`. Additionally, clean up redundant AI welcome code while preserving core AI assistant functionality.

## Technical Context

**Language/Version**: Python 3.x, Jinja2 templates
**Primary Dependencies**: Flask, Jinja2, jQuery (frontend)
**Storage**: SQLite (data/grading_system_v2.db) - no changes needed
**Testing**: Manual browser testing (login → verify floating button appears)
**Target Platform**: Web (Flask server, any modern browser)
**Project Type**: Web application (monolithic Flask + AI microservice)
**Performance Goals**: AI floating button visible within 1 second of page load
**Constraints**: Must not break other AI assistant functionality (document parsing, core generation)
**Scale/Scope**: Single template file fix (2 lines) + code cleanup

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **模块化解耦**: N/A - No new modules added, fix is within existing template
- [x] **微服务分离**: N/A - Not modifying AI microservice, only fixing frontend conditional
- [x] **前端设计一致性**: N/A - No UI changes, only fixing visibility condition
- [x] **批改器可扩展性**: N/A - Not touching grader code
- [x] **数据库迁移友好**: N/A - No database schema changes
- [x] **AI 能力分层**: N/A - Not changing AI capabilities or model selection
- [x] **AI 内容生成与缓存**: Existing caching preserved; verify after fix
- [x] **前端 AI 内容展示**: Existing streaming effects preserved; verify after fix
- [x] **AI 提示工程**: N/A - Not changing prompt templates
- [x] **个性化AI交互**: Verify personalization works after fix applied

**Result**: All applicable principles satisfied. This is a low-risk bug fix.

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-ai-welcome/
├── spec.md              # Feature specification (created)
├── plan.md              # This file
├── research.md          # Root cause documentation
├── data-model.md        # N/A (no data model changes)
├── contracts/           # N/A (no API changes)
│   └── api.md           # Existing endpoints documentation only
└── quickstart.md        # Testing instructions
```

### Source Code (affected files)

```text
templates/
├── base.html                           # BUG LOCATION: lines 403, 810
│                                       # Fix: session.get('user_id') → session.get('user')
├── components/
│   ├── ai_assistant_widget.html        # Floating button/chat (keep)
│   ├── ai_welcome_message.html         # Dashboard welcome (keep)
│   └── compact_welcome_message.html    # Top bar welcome (keep)
└── dashboard.html                      # Uses ai_welcome_message.html (no change)

static/js/
└── ai-welcome.js                       # Widget JS logic (review for cleanup)

blueprints/
└── ai_welcome.py                       # API endpoints (review for cleanup)

services/
├── ai_content_service.py               # Content generation (keep)
└── ai_prompts.py                       # Prompt templates (keep)
```

**Structure Decision**: Existing Flask monolith structure maintained. Only `templates/base.html` requires modification.

## Complexity Tracking

> No Constitution violations. This is a minimal 2-line fix.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Implementation Approach

### Phase 1: Bug Fix (Critical)

1. **Fix session key mismatch in base.html**:
   - Line 403: Change `session.get('user_id')` to `session.get('user')`
   - Line 810: Change `session.get('user_id')` to `session.get('user')`

2. **Verification**:
   - Start Flask app and AI assistant service
   - Log in as a user
   - Verify floating button appears in bottom-right corner
   - Click button to verify chat window opens
   - Test on dashboard, tasks, and other pages

### Phase 2: Code Cleanup (Secondary)

1. **Identify redundant code**:
   - Check for duplicate script loading
   - Verify no orphaned components
   - Ensure consistent session checks across templates

2. **Cleanup scope** (carefully preserve other AI functionality):
   - AI document parsing → KEEP
   - AI core generation → KEEP
   - AI welcome messages → KEEP (this is what we're fixing)
   - Any truly unused code → REMOVE

## Risk Assessment

**Low Risk**: This is a 2-line conditional fix. The code paths are:
- Before fix: `session.get('user_id')` returns `None`, widget never included
- After fix: `session.get('user')` returns user dict, widget included

**Rollback**: Revert the 2 line changes if any issues arise.
