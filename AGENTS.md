
# AGENTS.md — repo-specific guide for automated coding agents

Purpose: a short, actionable reference so an AI coding agent can make safe, high-value edits in this codebase.

Key takeaways (one-liner):
- Two main services (Flask app + AI microservice). Most UI/logic is in `app.py` + `blueprints/`; AI calls go through `ai_assistant.py` and `ai_utils/`.

Quick architecture & boundaries
- app.py (Flask) — UI, blueprint registration, SocketIO integration (uses gevent); serves on port 5010 when run with socketio.run(). See `app.py` for context processors and startup steps.
- blueprints/ — all user-facing routes live here. Each blueprint registers its own URL space (e.g. `classroom`, `student`, `library`, `admin`).
- grading_core/ — grader runtime: generated graders placed in `grading_core/graders/`; factory supports hot-reload via importlib.reload().
- ai_assistant.py + ai_utils/ — AI provider abstraction and helpers (OpenAI/Volcengine). Use these helpers rather than embedding API calls directly.

Developer flows (concrete commands)
- Run dev server (recommended for dev):
  - PowerShell: python app.py  # starts SocketIO/Flask app on port 5010
- Run AI microservice for AI features: python ai_assistant.py  # starts FastAPI on port 9011
- Docker compose: docker-compose up (see docker-compose.yml and Dockerfile[Base]).

Important conventions & patterns (must follow)
- Grader files: save to grading_core/graders/<id>.py. Graders must subclass BaseGrader and implement grade(student_dir, student_info) returning GradingResult. Use provided helpers: scan_files, smart_find, read_text_content, verify_command. See `grading_core/base.py` and `blueprints/ai_generator.py`.
- Template context: templates assume a `user` object is available (templates call user.get('username')). Use the app-level context processor in `app.py` (inject_user) or set g.user in `blueprints/auth.py` (load_logged_in_user) so templates never break.
- Blueprint auth pattern: `blueprints/auth.py` sets g.user from session and enforces redirects. Individual blueprint handlers still often check `if not g.user: return render_template('auth/login.html')`.
- DB access: prefer `extensions.db` (Database instance) and the helper methods in `database.py`. Some blueprints call `db.get_connection()` for raw SQL. Keep schema expectations in mind (look at data/*.db and docs/DATABASE_SCHEMA.md).

UI & routing notes agents commonly trip over
- Sidebar/menu items are defined in `templates/base.html`. They expect template `user` and `session['user']` to be present. If you add routes, ensure endpoint names and url_for(...) match blueprint names and are guarded by auth middleware.
- Student vs Teacher flows: there are separate blueprints for `student` (resource import/management) and `student_portal` (student-facing portal). Do not accidentally route teachers to student-facing endpoints — always check g.user and role flags (g.user.get('is_admin') or other fields).
- File/Resource pages: `blueprints/library.py` provides textbook pages and APIs. If you move textbook/catalog fields, update DB methods (db.create_textbook, db.get_textbooks) and front-end fetch paths (e.g. `/library/api/textbooks`).

Hot-reload & safe edit pattern
- When editing graders, write files into GRADERS_DIR and call GraderFactory.load_graders() (or rely on get_grader which reloads). Avoid changing BaseGrader signatures.

Common startup issues and debugging tips
- Templates failing with 'user' undefined: ensure `app.py` has a context_processor injecting 'user' (see current `create_app()` for inject_user) and `auth.load_logged_in_user` sets g.user from session. If templates still break, add defensive defaults (return {'user': {}}).
- SocketIO startup: app.py uses socketio.run(app, debug=True, port=5010). When running under flask run, socket handling differs — use python app.py for dev with SocketIO.
- Docker: ensure docker-compose maps ports correctly (5010 and 9011 for AI service) and env variables from docker.env are passed. If AI features fail, verify AI_ASSISTANT_BASE_URL in config.py.

Files to read first (quick tour)
- `app.py` — startup, context processors, blueprint registration, SocketIO configuration.
- `blueprints/*.py` — primary place to change routing/UI behavior (classroom.py, student.py, library.py, admin.py, ai_generator.py)
- `templates/base.html` — global layout, sidebar menu, user assumptions.
- `grading_core/` — grader runtime and templates.
- `ai_utils/` — call_ai_platform_chat and concurrency manager.
- `database.py` and `data/*.db` — DB schema and helper functions.

If you need automated edits
- Be explicit: which blueprint/template/database rows you want to add/change. I will generate a minimal patch that:
  1) updates route handlers in a blueprint,
  2) updates templates to use url_for correctly,
  3) updates DB helper functions in `database.py` and
  4) adds migration notes or creates SQL helper functions.

Quick contact points in repo (examples):
- Course / classroom: `blueprints/classroom.py`, templates under `templates/classroom/` (e.g. course_manage.html)
- Student import / lists: `blueprints/student.py`, templates under `templates/student/`
- Textbooks / resources: `blueprints/library.py`, `templates/library/textbooks.html`

Keep changes minimal and backward-compatible. When in doubt, add defensive guards (empty dicts for user) and small unit tests / manual smoke checks (start app.py and navigate to affected pages).


