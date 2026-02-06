# Implementation Plan: Grading Core Creation and Task Selection Improvements

**Branch**: `001-grading-core-creation` | **Date**: 2026-02-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-grading-core-creation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature improves the grading core creation and task selection workflows in an AI-powered auto-grading system. Primary improvements include:

1. **UI Reorganization**: Reorder form fields in both Logic Core and Direct AI Core creation forms to follow a logical workflow (documents → parameters → instructions → naming)
2. **AI Auto-Generation**: Add AI-powered core name generation with format `[Year/Season]-[CourseName]-[AssignmentType]批改核心`
3. **Course Name Auto-Fill**: Extract and populate course name from document metadata when both exam and grading criteria are selected
4. **Task Creation Bug Fix**: Fix core selection dropdown to display actual core names instead of "None"/"Generic Course"
5. **Naming Consistency**: Ensure both core types store consistent `name` and `course_name` values

**Technical Approach**:
- Frontend: Reorganize Jinja2 templates with Tailwind CSS, add JavaScript for AI auto-generation calls
- Backend: Add API endpoints for name/course auto-generation, update database queries to fix core selection
- AI Integration: Extend AI service to extract metadata and generate names from document content
- Service Layer: Create new service functions in `services/` for auto-generation logic

## Technical Context

**Language/Version**: Python 3.8+, Flask 2.x
**Primary Dependencies**: Flask, Jinja2, Tailwind CSS (CDN), OpenAI-compatible SDKs
**Storage**: SQLite (ai_tasks, file_assets tables)
**Testing**: pytest for backend, manual browser testing for frontend
**Target Platform**: Web application (Linux server)
**Project Type**: Web application (Flask + Jinja2 templates)
**Performance Goals**: Page load <2 seconds, auto-fill response <3 seconds
**Constraints**: Must preserve existing visual styling (glass-panel effects), no Flask imports in graders
**Scale/Scope**: ~50-100 concurrent users, ~1000 grading cores in database

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Functional Decoupling

| Requirement | Status | Notes |
|-------------|--------|-------|
| Blueprint Separation | ✅ PASS | Changes isolated to `blueprints/ai_generator.py` and `blueprints/grading.py` |
| Service Layer | ✅ PASS | New auto-generation logic will be in `services/ai_service.py` or new `services/core_metadata_service.py` |
| Grading Core Isolation | ✅ PASS | No changes to `grading_core/` internals, only metadata display |
| AI Abstraction | ✅ PASS | Will use existing `ai_utils/ai_helper.py` abstraction |

### Principle II: Hot-Pluggable Grading Architecture

| Requirement | Status | Notes |
|-------------|--------|-------|
| Grader Interface | ✅ PASS | No changes to `BaseGrader` interface |
| Factory Pattern | ✅ PASS | Updates to `GraderFactory.get_all_strategies()` to return proper course names |
| No Flask Context | ✅ PASS | Grading scripts remain unchanged |
| Deterministic Results | ✅ PASS | N/A - metadata extraction doesn't affect grading |

### Principle III: AI-Driven Generation with Structured Parsing

| Requirement | Status | Notes |
|-------------|--------|-------|
| Structured Prompts | ✅ PASS | Will add prompts for name/course extraction in `config.py` |
| Response Validation | ✅ PASS | Auto-generation responses validated before populating fields |
| Fallback Handling | ✅ PASS | Manual entry always available if AI fails |
| Vendor Neutrality | ✅ PASS | Uses existing AI abstraction layer |

### Principle IV: Frontend: Glassmorphic & Interactive Design

| Requirement | Status | Notes |
|-------------|--------|-------|
| Design Tokens | ✅ PASS | Will reuse existing Tailwind config from `base.html` |
| Glass Panel Pattern | ✅ PASS | Reorganization preserves `.glass-panel` classes |
| Visual Feedback | ✅ PASS | Loading states for AI auto-generation, error shake animations |
| Input Design | ✅ PASS | Reusing existing `bg-white/50` input styles |

### Principle V: Data Integrity & Grading Accuracy

| Requirement | Status | Notes |
|-------------|--------|-------|
| Atomic Operations | ✅ PASS | Metadata updates use existing database transactions |
| Audit Trail | ✅ PASS | AI auto-generation logged per NFR-001 |
| File Handling | ✅ PASS | No changes to file extraction logic |
| Excel Round-Trip | ✅ PASS | N/A - not affected by this feature |

### Principle VI: Dual-Service Isolation

| Requirement | Status | Notes |
|-------------|--------|-------|
| HTTP Protocol Only | ✅ PASS | Auto-generation calls AI service via HTTP |
| Graceful Degradation | ✅ PASS | Manual entry available if AI service down |
| Independent Deployment | ✅ PASS | No cross-service dependencies added |
| Error Boundaries | ✅ PASS | AI failures don't block form submission |

**Overall Result**: ✅ **PASS** - No constitution violations. All changes comply with architectural principles.

## Project Structure

### Documentation (this feature)

```text
specs/001-grading-core-creation/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Developer quickstart
├── contracts/           # Phase 1: API contracts
│   └── api.yaml         # OpenAPI spec for new endpoints
└── tasks.md             # Phase 2: Generated by /speckit.tasks
```

### Source Code (affected directories)

```text
# Frontend templates (reorganized)
templates/
├── components/
│   ├── form_logic.html      # Logic Core form - field reordering
│   └── form_direct.html     # Direct AI Core form - field reordering
├── ai_generator.html        # Main AI generator page
├── newClass.html            # Task creation page - core selection fix
└── modals/
    └── file_selector.html   # File selection modal (may need updates)

# Backend blueprints (new routes)
blueprints/
├── ai_generator.py          # Add /api/ai/generate_name, /api/ai/extract_course
└── grading.py               # Fix /api/strategies endpoint

# Service layer (business logic)
services/
├── ai_service.py            # Extend for name/course generation
└── core_metadata_service.py # NEW: Metadata extraction service

# AI utilities (prompt updates)
ai_utils/
└── ai_helper.py             # May need new method for metadata extraction

# Configuration (AI prompts)
config.py                    # Add NAME_GENERATION_PROMPT, COURSE_EXTRACTION_PROMPT

# Grading core (factory fix)
grading_core/
└── factory.py               # Fix get_all_strategies() to return proper course names
```

**Structure Decision**: This is a Flask web application with Jinja2 templates. Frontend changes are template reorganization without framework changes. Backend changes follow the service layer pattern with blueprint routes delegating to service functions.

## Complexity Tracking

> No constitution violations to justify. This section remains empty.

---

## Phase 0: Research & Technical Decisions

### Research Topics

1. **Document Metadata Structure**: Determine the exact JSON structure of `file_assets.meta_info` to extract course names
2. **AI Service Capabilities**: Verify AI service can extract structured metadata (course name, assignment type, year/season)
3. **GraderFactory Implementation**: Understand how `get_all_strategies()` currently returns data and why course names are missing
4. **Existing Auto-generation Patterns**: Review existing AI prompt patterns in `config.py` for consistency

### Best Practices to Research

1. **Form Field Ordering**: UX best practices for multi-step form flows
2. **AI Prompt Engineering**: Effective prompts for structured data extraction from Chinese documents
3. **Progressive Enhancement**: Graceful degradation patterns when AI services fail
4. **Database Query Optimization**: Efficient queries for core selection dropdown with course info

## Phase 1: Design Artifacts

### Data Model Changes

See [data-model.md](./data-model.md) for:
- Entity relationship diagram updates
- New API endpoint contracts
- Database query optimizations

### API Contracts

See [contracts/api.yaml](./contracts/api.yaml) for:
- `POST /api/ai/generate_name` - Generate core name from documents
- `POST /api/ai/extract_course` - Extract course name from documents
- `GET /api/strategies` - Updated to include course names

### Quickstart Guide

See [quickstart.md](./quickstart.md) for:
- Local development setup
- Testing AI auto-generation
- Verifying UI changes

---

## Phase 2: Implementation Order

Implementation will be organized by user story in `tasks.md` (generated by `/speckit.tasks`):

1. **User Story 1 (P1)**: Reorganized Core Creation UI
2. **User Story 3 (P1)**: Fixed Core Selection in Task Creation
3. **User Story 2 (P2)**: AI Auto-Generation of Core Names
4. **User Story 4 (P2)**: Unified Naming Convention

Each task will include:
- File-by-file change summary
- Testing checklist
- Acceptance criteria verification

---

## Dependencies & Integration Points

### External Dependencies
- **AI Assistant Service** (`ai_assistant.py`): Must be running for auto-generation features
- **File Asset Storage**: `file_assets` table must contain documents with metadata

### Internal Dependencies
- `ai_utils/ai_helper.py` - AI abstraction layer
- `database.py` - Database access layer
- `grading_core/factory.py` - Strategy enumeration

### Critical Path
1. Factory fix (US3) must be completed before US4 can be verified
2. AI prompts (US2) depend on research from Phase 0
3. UI reorganization (US1) can proceed in parallel with backend work

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AI service unavailable | Manual entry always available; clear error messaging |
| Incomplete metadata | Fallback to content analysis; manual override allowed |
| Visual regression | Use existing CSS classes; manual QA of all affected pages |
| Database migration needed | Use display-only fix with fallback labels (FR-008) |
| Performance degradation | Batch API calls; cache results where possible |
