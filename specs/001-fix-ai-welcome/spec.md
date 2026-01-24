# Feature Specification: Fix AI Welcome Message Display Bug

**Feature Branch**: `001-fix-ai-welcome`
**Created**: 2025-01-25
**Status**: Complete
**Input**: User description: "AI欢迎语助手的悬浮按钮和弹窗不显示，需要修复bug并清理冗余代码"

## Problem Statement

The AI welcome assistant feature (floating button and popup in the bottom-right corner) is not displaying after system startup. Investigation revealed a session key mismatch: the authentication system stores user data in `session['user']`, but the template checks for `session.get('user_id')` which never exists.

## Root Cause Analysis

**Location**: `templates/base.html` (lines 403 and 810)

**Issue**: The conditional checks use `session.get('user_id')` but the auth system (`blueprints/auth.py` line 36) stores user data as `session['user'] = user`

```python
# auth.py stores:
session['user'] = user  # A dict containing user info including 'id'

# base.html incorrectly checks:
{% if session.get('user_id') %}  # This is always None/False
```

**Impact**:
- The AI assistant floating widget (`ai_assistant_widget.html`) is never included
- The compact welcome message component is never included
- Users cannot see or interact with the AI assistant feature

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See AI Assistant Floating Button (Priority: P1)

As a logged-in user, I want to see the AI assistant floating button in the bottom-right corner of the page so that I can interact with the AI assistant.

**Why this priority**: This is the core functionality that is broken. Without the button visible, users cannot access the AI assistant at all.

**Independent Test**: Can be fully tested by logging in and verifying the floating button appears on the dashboard.

**Acceptance Scenarios**:

1. **Given** a user is logged in and viewing any non-admin page, **When** the page loads, **Then** the AI assistant floating button (robot icon) should be visible in the bottom-right corner
2. **Given** a user is not logged in, **When** viewing any page, **Then** the AI assistant floating button should not be visible
3. **Given** a user is logged in and on the admin page, **When** the page loads, **Then** the AI assistant floating button should not be visible

---

### User Story 2 - Interact with AI Assistant Chat (Priority: P2)

As a logged-in user, I want to click the floating button and open a chat window to communicate with the AI assistant.

**Why this priority**: Once the button is visible, users need to be able to interact with it.

**Independent Test**: Can be tested by clicking the button and verifying the chat window opens.

**Acceptance Scenarios**:

1. **Given** the floating button is visible, **When** I click it, **Then** the chat window should open with a smooth animation
2. **Given** the chat window is open, **When** I type a message and submit, **Then** the message should appear in the chat and AI should respond
3. **Given** the chat window is open, **When** I click the minimize button, **Then** the chat window should close

---

### User Story 3 - See AI Bubble Notifications (Priority: P3)

As a logged-in user, I want to receive proactive AI welcome messages as bubble notifications so that I get helpful tips and emotional support.

**Why this priority**: This is an enhancement feature that works alongside the main chat functionality.

**Independent Test**: Can be tested by waiting for automatic triggers or performing actions that trigger AI messages.

**Acceptance Scenarios**:

1. **Given** I am logged in and the AI decides to trigger a message, **When** the timer fires or an action triggers, **Then** a bubble message should appear above the floating button
2. **Given** a bubble message is showing, **When** I click the close button or wait 15 seconds, **Then** the bubble should fade away

---

### Edge Cases

- What happens when session expires mid-page? The widget should handle gracefully (API returns 401, UI shows appropriate message)
- What if the AI service is unavailable? Fallback messages should be displayed
- What happens on page navigation (SPA)? Widget state should persist

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display the AI assistant floating button for all logged-in users on non-admin pages
- **FR-002**: System MUST correctly check for user authentication using `session.get('user')` instead of `session.get('user_id')`
- **FR-003**: System MUST include the compact welcome message component in the top bar for logged-in users
- **FR-004**: System MUST hide the AI assistant widget on admin, login, and auth/login pages
- **FR-005**: The floating button MUST be visible, clickable, and positioned in the bottom-right corner (z-index 50)

### Code Cleanup Requirements

- **CR-001**: Remove redundant/unused AI welcome code while preserving other AI assistant functionality (document parsing, core generation)
- **CR-002**: Ensure no duplicate loading of AI welcome scripts
- **CR-003**: Verify all AI welcome related files are properly linked and not orphaned

### Key Components Involved

- **base.html**: Main template with the session check bug (lines 403, 810)
- **ai_assistant_widget.html**: The floating button and chat window component
- **compact_welcome_message.html**: Top bar welcome message component
- **ai-welcome.js**: JavaScript handling bubble display, chat, and triggers
- **ai_welcome.py**: Backend API endpoints for messages and chat
- **ai_content_service.py**: Service for generating AI welcome messages
- **ai_prompts.py**: System prompts for AI conversation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After logging in, the AI floating button is visible within 1 second of page load on all non-admin pages
- **SC-002**: Clicking the floating button opens the chat window within 300ms
- **SC-003**: AI chat messages receive responses within 10 seconds under normal conditions
- **SC-004**: 100% of logged-in users can see and interact with the AI assistant (no more hidden widget)

## Assumptions

- The AI service backend (`ai_assistant.py` on port 9011) is running and properly configured
- AI providers and models are configured in the admin panel
- The fix should not change any existing AI assistant functionality for document parsing or core generation
