# Implementation Plan: AI Welcome Message System

**Branch**: `001-ai-welcome-system` | **Date**: 2026-01-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-welcome-system/spec.md`

## Summary

Implement an AI-powered welcome message system that provides personalized, contextually-aware greetings to teachers. The system uses the existing AI assistant service (standard model) to generate welcome messages with emotional value and operational guidance. Messages are cached in the database with a 4-hour TTL and refreshed after write operations. Frontend displays messages with a streaming typewriter effect on first view and instant display on subsequent views, following the project's Frontend Design Guide (Neumorphism + Glassmorphism style).

## Technical Context

**Language/Version**: Python 3.11+, JavaScript (ES2022+)
**Primary Dependencies**: Flask (existing), FastAPI (ai_assistant.py), Tailwind CSS, Jinja2, SQLite
**Storage**: SQLite (existing database at `data/grading_system_v2.db`)
**Testing**: pytest (existing framework)
**Target Platform**: Web browser (modern browsers with localStorage support)
**Project Type**: Web application (Flask backend + Jinja2 templates)
**Performance Goals**:
- Welcome message display within 2 seconds (including AI generation)
- Cached messages display within 500ms
- Streaming animation completes within 3 seconds for 50 characters
- AI timeout threshold: 5 seconds, fallback within 1 second

**Constraints**:
- Must use existing AI assistant service (ai_assistant.py, port 9011)
- Must use "standard" capability model for generation
- Content validation: 10-200 characters, valid Chinese text
- 4-hour TTL for cached messages
- Graceful degradation on AI service failure

**Scale/Scope**:
- Peak concurrent users: <100
- Messages per user: 1 per page context (dashboard, tasks, student list, etc.)
- Database growth: ~100 records/day maximum

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **模块化解耦**: New module `services/ai_content_service.py` encapsulates AI content generation logic. Blueprint layer (`blueprints/`) calls service, service calls AI utils. Single-direction dependency maintained.
- [x] **微服务分离**: AI content generation uses existing AI assistant microservice (ai_assistant.py, port 9011) via HTTP REST API. No direct AI model calls from main app.
- [x] **前端设计一致性**: All UI components follow `templates/FRONTEND_GUIDE.md` - glass panel effect, Tailwind animations, indigo color scheme.
- [x] **批改器可扩展性**: Not applicable - this feature doesn't involve grading scripts.
- [x] **数据库迁移友好**: New table `ai_welcome_messages` uses `_migrate_table()` helper with default values for backward compatibility.
- [x] **AI 能力分层**: Uses "standard" capability model as specified. Fallback to default messages if standard model unavailable.
- [x] **AI 内容生成与缓存**: Messages cached in `ai_welcome_messages` table with 4-hour TTL. Service encapsulated in `services/ai_content_service.py`. Includes fallback strategy.
- [x] **前端 AI 内容展示**: Streaming typewriter effect on first view using JavaScript + CSS. `localStorage` tracks seen messages. Container auto-resizes with smooth transitions.
- [x] **AI 提示工程**: Prompts include 3-5 few-shot examples, structured input (JSON), clear output format, time/user stats context. Defined in `services/ai_prompts.py`.

**Gate Status**: ✅ PASSED - No violations, all principles aligned.

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-welcome-system/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.yaml         # OpenAPI spec for welcome message endpoints
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Existing structure - leveraging existing patterns
autoCorrecting/
├── app.py                      # Main Flask app - register new blueprint
├── config.py                   # Config - add AI content cache TTL setting
├── database.py                 # Database - add ai_welcome_messages table migration
├── blueprints/
│   ├── main.py                 # Dashboard - add welcome message integration
│   └── ai_welcome.py           # NEW: Blueprint for welcome message API endpoints
├── services/
│   ├── ai_content_service.py   # NEW: AI content generation and caching service
│   └── ai_prompts.py           # NEW: AI prompt templates for welcome/guidance messages
├── templates/
│   ├── dashboard.html          # MODIFY: Replace static welcome with AI component
│   ├── components/
│   │   └── ai_welcome_message.html  # NEW: Reusable AI welcome component
│   └── static/
│       └── js/
│           └── ai-welcome.js   # NEW: Streaming animation and localStorage tracking
└── tests/
    └── ai_welcome/              # NEW: Test suite for welcome system
        ├── test_service.py
        └── test_api.py
```

**Structure Decision**: Leveraging existing Flask + Jinja2 architecture. New blueprint `ai_welcome.py` follows existing pattern (similar to `admin.py`, `ai_generator.py`). Service layer separation maintains Principle I (Modular Decoupling). Frontend component reusability enables cross-page display (dashboard + other pages).

## Phase 0: Research

### Research Tasks

| # | Task | Status | Decision |
|---|------|--------|----------|
| 1 | Explore existing AI service integration patterns | ✅ Complete | Use `ai_service.call_ai_chat()` pattern from existing code |
| 2 | Determine localStorage key naming convention | ✅ Complete | `ai_welcome_seen_{page_context}_{message_id}` |
| 3 | Research streaming animation implementation | ✅ Complete | CSS keyframes + JS character-by-character reveal |
| 4 | Define fallback message templates by time-of-day | ✅ Complete | Morning (6-11), Afternoon (12-17), Evening (18-22), Night (23-5) |
| 5 | Validate database migration approach | ✅ Complete | Use `_migrate_table()` with `ALTER TABLE` for new columns |

### Key Decisions

**Decision 1: AI Service Integration Pattern**
- **Choice**: Reuse existing `ai_service.call_ai_chat()` from `services/ai_service.py`
- **Rationale**: Maintains consistency with existing AI integration, already handles error cases and timeout
- **Alternatives considered**: Direct HTTP calls to ai_assistant.py (rejected - duplicates code), WebSocket (rejected - overkill for simple text generation)

**Decision 2: Streaming Animation Approach**
- **Choice**: JavaScript-based character-by-character reveal with CSS transitions
- **Rationale**: Cross-browser compatible, no additional dependencies, works with SPA navigation
- **Alternatives considered**: CSS-only animation (rejected - harder to control dynamic content length), Server-Sent Events (rejected - adds complexity)

**Decision 3: Cache Key Strategy**
- **Choice**: Composite key: `(user_id, page_context, time_period)` where time_period = 4-hour blocks
- **Rationale**: Balances personalization with cache efficiency. Time-based refresh ensures time-sensitive greetings remain relevant
- **Alternatives considered**: Per-user only (rejected - doesn't handle different pages), Global only (rejected - not personalized)

**Decision 4: Content Validation Rules**
- **Choice**: Length check (10-200 chars) + Chinese character range detection (\u4e00-\u9fff)
- **Rationale**: Simple, fast, prevents obviously malformed output. Few false positives.
- **Alternatives considered**: Sentiment analysis (rejected - may filter valid encouraging messages), Keyword blocking (rejected - too restrictive for educational context)

## Phase 1: Design

### Data Model

See [`data-model.md`](./data-model.md) for complete entity definitions.

**Key Entities**:
- `ai_welcome_messages` - Table for cached AI-generated messages
- `WelcomeMessage` - Python dataclass for message representation
- `MessageContext` - Python dataclass for AI prompt context

### API Contracts

See [`contracts/api.yaml`](./contracts/api.yaml) for OpenAPI specification.

**Key Endpoints**:
- `GET /api/welcome/messages` - Fetch welcome message for current page/context
- `POST /api/welcome/messages/refresh` - Trigger message regeneration (after write operations)
- `GET /api/welcome/fallback` - Get time-based fallback message (client-side or server-side)

### Quickstart Guide

See [`quickstart.md`](./quickstart.md) for development setup and testing instructions.

## Implementation Phases

### Phase 1: Backend Foundation

1. **Database Migration** (`database.py`)
   - Add `ai_welcome_messages` table with `_migrate_table()`
   - Fields: id, user_id, page_context, message_content, created_at, expires_at, context_snapshot

2. **AI Prompts Module** (`services/ai_prompts.py`)
   - Define `WELCOME_PROMPT_TEMPLATE` with few-shot examples
   - Define page-specific templates (tasks, student_list, ai_generator, export)
   - Implement time-of-day fallback messages

3. **AI Content Service** (`services/ai_content_service.py`)
   - `generate_welcome_message(user_id, page_context, stats)` - main generation function
   - `get_cached_message(user_id, page_context)` - cache retrieval
   - `invalidate_cache(user_id, page_context)` - post-write invalidation
   - `validate_message(content)` - content validation
   - `get_fallback_message(time_of_day)` - fallback generation

4. **Blueprint** (`blueprints/ai_welcome.py`)
   - `GET /api/welcome/messages` - public endpoint for fetching
   - `POST /api/welcome/messages/refresh` - regeneration trigger
   - Integration with existing auth (require login)

### Phase 2: Frontend Components

1. **Welcome Component** (`templates/components/ai_welcome_message.html`)
   - Glass panel container matching FRONTEND_GUIDE.md
   - Dynamic height with smooth transitions
   - Loading state indicator

2. **Streaming Animation** (`static/js/ai-welcome.js`)
   - `typewriter()` function for character-by-character reveal
   - `localStorage` tracking: `ai_welcome_seen_{context}`
   - Auto-detect first view vs. repeat view

3. **Dashboard Integration** (`templates/dashboard.html`)
   - Replace static "今天也是充满效率的一天..." with AI component
   - Pass context variables (stats, recent actions)

4. **Other Pages Integration** (`templates/base.html` topbar)
   - Add compact welcome message slot in topbar
   - Show only on relevant pages (not login, not admin)

### Phase 3: Write Operation Triggers

Integrate cache refresh into existing write operations:
- `blueprints/ai_generator.py` - after grader generation
- `blueprints/main.py` - after class creation
- `blueprints/student.py` - after student import
- `blueprints/grading.py` - after submission

Trigger: call `ai_content_service.invalidate_cache(user_id, 'dashboard')`

### Phase 4: Testing & Refinement

1. **Unit Tests** (`tests/ai_welcome/`)
   - Test message generation with mock AI
   - Test cache TTL logic
   - Test content validation
   - Test fallback generation

2. **Integration Tests**
   - Test end-to-end flow with real AI service
   - Test timeout/fallback behavior
   - Test concurrent access

3. **Manual Testing**
   - Verify streaming animation on first view
   - Verify instant display on refresh
   - Verify time-of-day fallback
   - Verify cross-page guidance

## Dependencies

### New Python Dependencies
- None (uses existing dependencies)

### New JavaScript Dependencies
- None (uses vanilla JS + existing Tailwind)

### External Services
- `ai_assistant.py` (port 9011) - existing AI microservice

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI service slow/timeout | High | 5-second timeout + fallback messages, stale cache serving |
| Poor quality AI output | Medium | Content validation, few-shot examples in prompts |
| Streaming animation bugs | Low | Graceful fallback to instant display, localStorage failure handling |
| Cache bloat | Low | 4-hour TTL auto-cleanup, simple table structure |

## Rollout Plan

1. **Phase 1**: Backend foundation (database, service, API) - deploy to staging
2. **Phase 2**: Frontend dashboard integration - test with subset of users
3. **Phase 3**: Cross-page rollout - enable for all pages
4. **Phase 4**: Write operation integration - enable cache refresh triggers
5. **Phase 5**: Full rollout - monitor AI costs, adjust TTL if needed

## Success Metrics

- Message display latency < 2s (p95)
- Cache hit rate > 80% (reduces AI calls)
- Streaming animation completion < 3s
- User feedback > 90% positive (optional feedback collection)
- Zero increase in page load time for cached messages
