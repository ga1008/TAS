# Research: AI Welcome Message Display Bug

**Feature**: 001-fix-ai-welcome
**Date**: 2025-01-25
**Status**: Complete

## Executive Summary

The AI welcome assistant floating button and popup are not displaying due to a session key mismatch. The authentication system stores user data in `session['user']`, but the template conditional checks for `session.get('user_id')` which never exists.

## Root Cause Analysis

### Finding 1: Session Key Mismatch

**Decision**: Fix the template conditional to use `session.get('user')` instead of `session.get('user_id')`

**Rationale**:
- The auth blueprint (`blueprints/auth.py` line 36) stores: `session['user'] = user`
- The user object is a dictionary containing `{'id': ..., 'username': ..., ...}`
- The template checks `session.get('user_id')` which is never set
- Result: The conditional always evaluates to False, hiding the widget

**Evidence**:
```python
# blueprints/auth.py - How user is stored
session['user'] = user  # user is a dict with 'id' key

# templates/base.html - Incorrect check (line 403, 810)
{% if session.get('user_id') %}  # This is always None
```

**Alternatives Considered**:
1. **Set `session['user_id']` in auth.py**: Would require changing all auth code; more invasive
2. **Use `session.get('user', {}).get('id')`**: More defensive but unnecessary complexity
3. **Fix template to use `session.get('user')`**: Minimal change, consistent with existing pattern

### Finding 2: Affected Locations

**Decision**: Fix both occurrences in `templates/base.html`

| Line | Current Code | Purpose |
|------|--------------|--------|
| 403 | `{% if session.get('user_id') and request.path not in ... %}` | Compact welcome message in top bar |
| 810 | `{% if session.get('user_id') and request.path not in ... %}` | AI assistant floating widget |

**Rationale**: Both lines use the same pattern and serve the same purpose (showing AI components to logged-in users).

### Finding 3: Code Architecture Review

**Decision**: No redundant code needs removal for the core fix

**Components Reviewed**:

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| ai_assistant_widget.html | templates/components/ | KEEP | Floating button + chat window |
| ai_welcome_message.html | templates/components/ | KEEP | Dashboard inline message |
| compact_welcome_message.html | templates/components/ | KEEP | Top bar compact message |
| ai-welcome.js | static/js/ | KEEP | Widget interaction logic |
| ai_welcome.py | blueprints/ | KEEP | API endpoints for messages |
| ai_content_service.py | services/ | KEEP | Content generation service |
| ai_prompts.py | services/ | KEEP | AI prompt templates |

**Rationale**: All components serve distinct purposes in the AI welcome system. The dashboard.html has a commented-out script tag (line 326) which is correctly disabled since base.html now loads the script globally.

## Technical Details

### Session Structure

```python
# After login, session contains:
session['user'] = {
    'id': 1,
    'username': 'teacher',
    'role': 'teacher',
    # ... other fields
}
```

### Widget Display Flow

1. User logs in → `session['user']` set in auth.py
2. User visits page → base.html renders
3. Template checks `session.get('user')` (after fix)
4. If user logged in and not on admin/login page:
   - Include `ai_assistant_widget.html` (floating button)
   - Include `compact_welcome_message.html` (top bar)
5. `ai-welcome.js` initializes widget behavior
6. Widget fetches messages from `/api/welcome/messages`

### Exclusion Pages

Widget is correctly hidden on:
- `/admin` - Admin control panel
- `/login` - Login page
- `/auth/login` - Auth login endpoint

## Verification Plan

### Pre-fix State
- [ ] Start app, log in → No floating button visible
- [ ] Check browser console → No JS errors from ai-welcome.js (because element doesn't exist)

### Post-fix State
- [ ] Start app, log in → Floating button visible in bottom-right
- [ ] Click button → Chat window opens
- [ ] Type message → AI responds
- [ ] Visit admin page → Button hidden
- [ ] Log out → Button hidden

## Conclusion

This is a straightforward 2-line fix with no architectural changes required. The root cause is a simple key name mismatch introduced when the AI welcome feature was added.
