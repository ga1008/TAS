# Implementation Plan: Grading Core Improvements

**Branch**: `001-grading-core-improvements` | **Date**: 2026-02-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-grading-core-improvements/spec.md`

## Summary

This feature improves the grading core system in two ways:
1. **Extra Prompt Support for Logic Cores**: Add an extra prompt textarea to the AI generator page, allowing teachers to provide additional guidance (e.g., file matching flexibility) when generating logic cores.
2. **Fix Volcengine Multimodal Integration**: Fix runtime errors in AI direct cores by properly implementing base64 encoding for images and Files API uploads for videos/PDFs according to Volcengine's ARC documentation.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**: Flask 2.x, Volcengine SDK, OpenAI-compatible SDKs, Jinja2, Tailwind CSS
**Storage**: SQLite (via `database.py` - direct SQL, not ORM)
**Testing**: pytest (unit tests for services, integration tests for blueprints)
**Target Platform**: Linux server (Docker Compose deployment)
**Project Type**: Web application (Flask backend + Jinja2 frontend)
**Performance Goals**:
- AI direct core grading: 60 seconds for 5 files, 120 seconds for 10 files
- File upload: 60 seconds per file timeout
**Constraints**:
- No direct Flask imports in graders (constitution requirement)
- Service layer must contain all business logic
- Glassmorphic design system for frontend
- Volcengine file size limit: 512 MB per file
- Media file limits: 5 soft, 10 hard
**Scale/Scope**:
- Database fields: Add `extra_prompt` column to `ai_tasks` table
- Frontend components: Update AI generator form
- Backend services: Update `ai_generator.py`, `direct_grader_template.py`
- Files to modify: ~5 files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Functional Decoupling** | ✅ PASS | Blueprint routes delegate to service layer. No direct database access in routes. |
| **II. Hot-Pluggable Grading Architecture** | ✅ PASS | Generated graders inherit from `BaseGrader`, no Flask imports in graders. |
| **III. AI-Driven Generation with Structured Parsing** | ✅ PASS | AI responses validated via AST parsing. Vendor abstraction via `ai_helper.py`. |
| **IV. Frontend: Glassmorphic & Interactive Design** | ✅ PASS | New textarea will use `.glass-panel` class with consistent styling. |
| **V. Data Integrity & Grading Accuracy** | ✅ PASS | Atomic score updates, file upload errors logged and handled gracefully. |
| **VI. Dual-Service Isolation** | ✅ PASS | AI operations via HTTP to `ai_assistant.py` microservice. |

**Gates Status**: All gates passed. No constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-grading-core-improvements/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.md           # API contract updates
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── blueprints/
│   └── ai_generator.py      # Extra prompt field handling (FR-001, FR-002, FR-005)
├── services/
│   ├── ai_service.py        # Integrate extra_prompt into generation (FR-002)
│   └── file_service.py      # File filtering logic (FR-010, FR-011)
├── grading_core/
│   ├── direct_grader_template.py  # Fix multimodal handling (FR-006, FR-007, FR-008, FR-009)
│   └── base.py              # Existing: BaseGrader class
├── templates/
│   ├── ai_generator.html    # Add extra prompt textarea (FR-001, FR-013, FR-014)
│   └── base.html            # Existing: Tailwind config
├── database.py              # Add migration for extra_prompt column
└── migrations/
    └── add_extra_prompt.sql # Database migration script

frontend/ (N/A - using Jinja2 templates)
└── N/A - Frontend is server-rendered via Jinja2

tests/
├── unit/
│   ├── test_ai_service.py           # Test extra_prompt integration
│   └── test_direct_grader_template.py # Test multimodal handling
└── integration/
    └── test_ai_generator.py          # Test form submission with extra prompt
```

**Structure Decision**: Web application with Flask backend and Jinja2 server-side rendering. No separate frontend build process. All UI components are in `templates/` directory. Business logic in `services/`, routes in `blueprints/`.

## Complexity Tracking

> No constitution violations requiring justification.

## Phase 0: Research & Technology Decisions

### Unknowns to Research

1. **Volcengine Files API Integration** (NEEDS CLARIFICATION):
   - Current implementation uses `VolcFileManager` but may have issues
   - Need to verify correct API usage for image base64 vs video file_id
   - According to ARC_doc.md, files >50 MB or reusable files should use Files API

2. **Database Migration Strategy** (NEEDS CLARIFICATION):
   - Current `database.py` uses direct SQL, not ORM
   - Need to determine migration approach (manual SQL vs script)
   - Existing `ai_tasks` table has `extra_desc` - need to add `extra_prompt`

3. **Base64 Encoding for Volcengine** (NEEDS CLARIFICATION):
   - ARC_doc.md shows two approaches: base64 data URLs OR Files API
   - Clarification specified: Images use base64, videos/PDFs use Files API
   - Need to verify correct format for Volcengine Responses API

4. **Glassmorphic Design Implementation** (NEEDS CLARIFICATION):
   - Need to examine existing `.glass-panel` class in `templates/base.html`
   - Ensure consistent styling for new textarea

### Research Tasks

1. **Task**: Research Volcengine Files API integration
   - **Goal**: Understand correct usage for images (base64) vs videos/PDFs (file_id)
   - **Sources**: `ai_utils/ARC_doc.md`, `ai_utils/volc_file_manager.py`, `ai_utils/ai_helper.py`
   - **Output**: Decision on file handling approach

2. **Task**: Research database migration approach
   - **Goal**: Determine how to add `extra_prompt` column to `ai_tasks` table
   - **Sources**: `database.py`, existing migration patterns in codebase
   - **Output**: Migration script or approach

3. **Task**: Research existing glassmorphic design system
   - **Goal**: Understand `.glass-panel` styling patterns
   - **Sources**: `templates/base.html`, `templates/FRONTEND_GUIDE.md`
   - **Output**: Design spec for extra prompt textarea

## Phase 1: Design & Contracts

### Data Model

**Entities to Update**:

1. **ai_tasks** table:
   - **New field**: `extra_prompt` (TEXT, nullable)
   - **Purpose**: Store extra prompt for logic core generation
   - **Note**: `extra_desc` already exists for direct cores, reusing pattern

2. **No new entities** - only extending existing `ai_tasks` table

### API Contracts

**Existing endpoints to modify**:

1. **POST /api/create_grader_task**
   - **Add**: `extra_prompt` form field (optional, max 2000 chars)
   - **Validation**: Soft limit with warning if exceeded
   - **Response**: No change

2. **POST /api/create_direct_grader**
   - **No change** - uses `extra_instruction` field (different use case)

### Frontend Components

**Templates to update**:

1. **ai_generator.html**:
   - Add `<textarea>` for extra prompt input
   - Class: `.glass-panel`, `bg-white/50`, consistent padding
   - Character counter (show warning at 2000)
   - Placeholder text with examples

### Quick Start Guide

After implementation, users can:
1. Visit `/ai_generator` page
2. Fill in task name, select exam/standard files
3. Enter extra prompt (optional) with file matching guidance
4. Submit to generate logic core with enhanced file matching
5. Create AI direct cores that properly handle images, videos, and PDFs
