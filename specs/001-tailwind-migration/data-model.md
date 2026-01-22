# Data Model: Frontend Tailwind CSS Migration

**Feature**: 001-tailwind-migration
**Date**: 2026-01-22

## Overview

本次迁移不涉及数据库变更，此文档记录前端文件的结构化清单和转换映射关系。

## File Inventory

### HTML Templates (37 files)

#### Core Layout
| File | Lines | Tailwind Config | Inline Styles | Priority |
|------|-------|-----------------|---------------|----------|
| `templates/base.html` | ~200 | ✅ Central | ✅ | P0 |
| `templates/dashboard.html` | ~150 | Inherits | ✅ glass-panel | P1 |
| `templates/index.html` | ~100 | Inherits | ✅ glass-panel | P1 |

#### Authentication
| File | Lines | Tailwind Config | Inline Styles | Priority |
|------|-------|-----------------|---------------|----------|
| `templates/login.html` | ~100 | ✅ Standalone | ✅ | P1 |
| `templates/admin/login.html` | ~100 | ✅ Standalone | ✅ | P1 |

#### Grading System
| File | Lines | Tailwind Config | Inline Styles | Priority |
|------|-------|-----------------|---------------|----------|
| `templates/grading.html` | ~300 | Inherits | ✅ Extensive | P1 |
| `templates/ai_generator.html` | ~200 | Inherits | ✅ glass-panel | P2 |
| `templates/ai_core_list.html` | ~150 | Inherits | ✅ | P2 |
| `templates/grader_detail.html` | ~150 | ✅ Standalone | ✅ | P2 |

#### Class & Student Management
| File | Lines | Tailwind Config | Inline Styles | Priority |
|------|-------|-----------------|---------------|----------|
| `templates/newClass.html` | ~150 | Inherits | ✅ glass inputs | P2 |
| `templates/tasks.html` | ~200 | Inherits | ✅ class cards | P2 |
| `templates/student_detail.html` | ~150 | ✅ Standalone | ✅ | P2 |
| `templates/student/list.html` | ~100 | Inherits | Minimal | P3 |
| `templates/student/import.html` | ~100 | Inherits | Minimal | P3 |
| `templates/student/detail.html` | ~100 | Inherits | Minimal | P3 |

#### Library & Export
| File | Lines | Tailwind Config | Inline Styles | Priority |
|------|-------|-----------------|---------------|----------|
| `templates/library/index.html` | ~250 | Inherits | ✅ Extensive | P2 |
| `templates/file_manager.html` | ~150 | Inherits | ✅ | P2 |
| `templates/export.html` | ~150 | ✅ Standalone | ✅ | P2 |

#### Other Pages
| File | Lines | Tailwind Config | Inline Styles | Priority |
|------|-------|-----------------|---------------|----------|
| `templates/intro.html` | ~100 | Inherits | ✅ | P3 |
| `templates/jwxt_connect.html` | ~100 | Inherits | Minimal | P3 |
| `templates/admin/dashboard.html` | ~150 | Inherits | ✅ | P3 |

#### Components (14 files)
| File | Inline Styles | Priority |
|------|---------------|----------|
| `components/notification_center.html` | ✅ Extensive | P1 |
| `components/ai_welcome_message.html` | ✅ | P1 |
| `components/compact_welcome_message.html` | ✅ | P1 |
| `components/stats/stat_card.html` | ✅ | P2 |
| `components/stats/activity_item.html` | ✅ | P2 |
| `components/stats/quick_action.html` | ✅ | P2 |
| `components/gen_tabs.html` | Minimal | P3 |
| `components/gen_modals.html` | Minimal | P3 |
| `components/gen_task_list.html` | Minimal | P3 |
| `components/gen_scripts.html` | None | P3 |
| `components/gen_form_scripts.html` | None | P3 |
| `components/form_logic.html` | Minimal | P3 |
| `components/form_direct.html` | Minimal | P3 |
| `components/jwxt_login_modal.html` | Minimal | P3 |
| `components/topbar/*.html` | Minimal | P3 |

### CSS Files

#### To Migrate & Delete
| File | Lines | Purpose | Complexity |
|------|-------|---------|------------|
| `static/css/style.css` | 431 | Core UI framework | High |
| `static/css/ai_chat.css` | 841 | AI chat interface | High |

#### To Delete (Bootstrap)
| File | Purpose |
|------|---------|
| `static/css/bootstrap.css` | Full framework |
| `static/css/bootstrap.min.css` | Minified |
| `static/css/bootstrap-grid.css` | Grid only |
| `static/css/bootstrap-grid.min.css` | Grid minified |
| `static/css/bootstrap-reboot.css` | Reset |
| `static/css/bootstrap-reboot.min.css` | Reset minified |
| `static/css/bootstrap-utilities.css` | Utilities |
| `static/css/bootstrap-utilities.min.css` | Utilities minified |
| `static/css/bootstrap*.rtl.css` | RTL variants |
| `static/css/*.map` | Source maps |

#### To Keep
| File | Purpose |
|------|---------|
| `static/css/all.min.css` | FontAwesome icons |

### JavaScript Files

#### Requires Update
| File | Lines | Inline Styles | Action |
|------|-------|---------------|--------|
| `static/js/modules/ai-chat/chat-ui.js` | 600 | 30+ instances | Convert static styles to classes |
| `static/js/modules/ui/image-parser.js` | 199 | 1 instance | Minor update |

#### No Changes Needed
| File | Lines | Purpose |
|------|-------|---------|
| `static/js/main.js` | 87 | Module orchestrator |
| `static/js/script.js` | 682 | Page scripts |
| `static/js/spa_router.js` | 447 | SPA navigation |
| `static/js/ai-welcome.js` | ~100 | Welcome animation |
| `static/js/admin.js` | ~100 | Admin panel |
| `static/js/tools.js` | ~50 | Utilities |
| `static/js/modules/*.js` | Various | Other modules |

## CSS Class Mapping

### style.css → Tailwind

```
.card-glass
  → bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg border border-white/20

.btn-primary
  → bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium
    rounded-lg px-4 py-2 hover:shadow-lg hover:-translate-y-0.5
    transition-all duration-300

.btn-secondary
  → bg-white/50 text-slate-700 border border-slate-200 rounded-lg px-4 py-2
    hover:bg-white/80 transition-all duration-300

.form-control
  → w-full bg-white/50 border border-slate-200 rounded-lg px-4 py-2.5
    focus:ring-2 focus:ring-indigo-500 focus:border-transparent
    transition-all duration-300

.navbar-custom
  → bg-white/80 backdrop-blur-md shadow-sm border-b border-white/20

.sidebar
  → fixed left-0 top-0 h-screen w-64 bg-white/80 backdrop-blur-xl
    border-r border-white/20 shadow-xl

.fab-button
  → fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg
    bg-gradient-to-r from-indigo-500 to-purple-600 text-white
    hover:shadow-xl hover:scale-110 transition-all duration-300
```

### ai_chat.css → Tailwind

```
.ai-chat-fab
  → fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg z-50
    bg-gradient-to-r from-indigo-500 to-purple-600 text-white
    hover:shadow-xl hover:scale-110 transition-all duration-300
    flex items-center justify-center cursor-pointer

.ai-chat-modal
  → fixed inset-0 bg-black/50 backdrop-blur-sm z-50
    flex items-center justify-center

.ai-chat-container
  → bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl
    w-[90vw] max-w-4xl h-[80vh] flex flex-col overflow-hidden

.ai-chat-header
  → flex items-center justify-between px-6 py-4
    border-b border-slate-200 bg-gradient-to-r from-indigo-500 to-purple-600
    text-white rounded-t-2xl

.ai-chat-messages
  → flex-1 overflow-y-auto p-6 space-y-4

.message-user
  → ml-auto max-w-[80%] bg-indigo-500 text-white
    rounded-2xl rounded-br-md px-4 py-3

.message-assistant
  → mr-auto max-w-[80%] bg-white/80 backdrop-blur border border-slate-200
    rounded-2xl rounded-bl-md px-4 py-3

.ai-chat-input
  → flex items-center gap-3 px-6 py-4 border-t border-slate-200
    bg-white/50 rounded-b-2xl
```

## Validation Checklist

### Per-File Validation
- [ ] No `<link>` to style.css or ai_chat.css
- [ ] No `<link>` to bootstrap*.css
- [ ] No standalone `tailwind.config` (except base.html)
- [ ] No inline `<style>` blocks (except necessary animations)
- [ ] All visual elements use Tailwind classes
- [ ] Bootstrap JS components still functional

### Global Validation
- [ ] All pages render correctly
- [ ] All modals open/close properly
- [ ] All tooltips display correctly
- [ ] SPA navigation works
- [ ] Responsive layouts intact
- [ ] Animations smooth
- [ ] No console errors
