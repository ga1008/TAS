# Quickstart: Testing AI Welcome Message Fix

**Feature**: 001-fix-ai-welcome
**Date**: 2025-01-25

## Prerequisites

1. Python 3.x installed
2. Dependencies installed: `pip install -r requirements.txt`
3. AI service configured in admin panel (optional, for full AI responses)

## Quick Start

### 1. Start the Services

```bash
# Terminal 1: Start main Flask app
python app.py
# Runs on http://127.0.0.1:5010

# Terminal 2: Start AI assistant service (optional for full AI functionality)
python ai_assistant.py
# Runs on http://127.0.0.1:9011
```

### 2. Test the Fix

1. **Open browser**: Navigate to `http://127.0.0.1:5010`

2. **Log in**: Use test credentials (or create a user)
   - Default: Check database or create via admin panel

3. **Verify floating button**:
   - [ ] Look for robot icon button in bottom-right corner
   - [ ] Button should be visible on dashboard
   - [ ] Button should be visible on other pages (tasks, library, etc.)

4. **Test chat functionality**:
   - [ ] Click the floating button
   - [ ] Chat window should open with animation
   - [ ] Type a message and press Enter
   - [ ] AI should respond (or fallback message if AI service not running)

5. **Verify exclusions**:
   - [ ] Navigate to `/admin/` → Button should NOT appear
   - [ ] Log out → Button should NOT appear

## Expected Results

### Before Fix

- No floating button visible anywhere
- `ai_assistant_widget.html` never included in page
- JavaScript `ai-welcome.js` finds no elements to attach to

### After Fix

- Floating robot button visible in bottom-right corner
- Click opens chat window
- AI responds to messages (with AI service) or shows fallback
- Button hidden on admin/login pages

## Troubleshooting

### Button still not visible

1. Check browser console for JavaScript errors
2. Verify you're logged in (session exists)
3. Check page source for `ai-widget-root` element
4. Ensure not on excluded pages (/admin, /login)

### AI not responding

1. Check if `ai_assistant.py` is running on port 9011
2. Verify AI provider configured in admin panel
3. Check AI service logs for errors
4. Fallback message should still appear

### Styling issues

1. Clear browser cache
2. Verify Tailwind CSS loading
3. Check z-index conflicts (widget uses z-50)

## Test Commands

```bash
# Check if Flask app is running
curl http://127.0.0.1:5010/

# Check if AI service is running
curl http://127.0.0.1:9011/health

# Test welcome API (requires valid session)
curl -b "session=..." http://127.0.0.1:5010/api/welcome/messages
```

## Related Files

- `templates/base.html` (lines 403, 810) - The fix location
- `templates/components/ai_assistant_widget.html` - Floating widget HTML
- `static/js/ai-welcome.js` - Widget JavaScript
- `blueprints/ai_welcome.py` - API endpoints
