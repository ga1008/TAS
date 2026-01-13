import sqlite3
import threading
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config


class Database:
    def __init__(self, db_path=Config.DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        # 初始化数据库表结构
        self.init_db_tables()

    def get_connection(self):
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def close(self):
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection

    def init_db_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. 管理员用户表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           username      TEXT NOT NULL UNIQUE,
                           password_hash TEXT,
                           is_admin      BOOLEAN   DEFAULT 0,
                           has_seen_help      BOOLEAN   DEFAULT 0,
                           created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')

        # 2. 班级表 (批改业务)
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS classes
                       (
                           id             INTEGER PRIMARY KEY AUTOINCREMENT,
                           name           TEXT,
                           course         TEXT,
                           workspace_path TEXT,
                           strategy       TEXT DEFAULT 'server_config_2025',
                           created_by     INTEGER DEFAULT 1
                       )
                       ''')

        # 3. 学生表 (批改业务)
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS students
                       (
                           id         INTEGER PRIMARY KEY AUTOINCREMENT,
                           student_id TEXT,
                           name       TEXT,
                           gender     TEXT,
                           class_id   INTEGER
                       )
                       ''')

        # 4. 成绩表 (升级版：支持动态分项)
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS grades
                       (
                           id             INTEGER PRIMARY KEY AUTOINCREMENT,
                           student_id     TEXT,
                           class_id       INTEGER,
                           total_score    REAL,
                           score_details  TEXT,          -- 新增：存储 JSON 格式的分项成绩
                           deduct_details TEXT,
                           status         TEXT,
                           filename       TEXT,
                           UNIQUE (student_id, class_id) -- 确保每个学生在每个班级只有一条记录
                       )
                       ''')

        # 5. AI 厂商表 (AI Admin)
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS ai_providers
                       (
                           id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                           name                    TEXT NOT NULL UNIQUE,
                           provider_type           TEXT NOT NULL,
                           base_url                TEXT,
                           api_key                 TEXT NOT NULL,
                           max_concurrent_requests INTEGER   DEFAULT 3,
                           is_enabled              BOOLEAN   DEFAULT 1,
                           created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')

        # 6. AI 模型表 (AI Admin)
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS ai_models
                       (
                           id             INTEGER PRIMARY KEY AUTOINCREMENT,
                           provider_id    INTEGER NOT NULL,
                           model_name     TEXT    NOT NULL,
                           capability     TEXT    NOT NULL CHECK (capability IN ('standard', 'thinking', 'vision')),
                           weight         INTEGER   DEFAULT 50,
                           can_force_json BOOLEAN   DEFAULT 0,
                           is_enabled     BOOLEAN   DEFAULT 1,
                           created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (provider_id) REFERENCES ai_providers (id) ON DELETE CASCADE
                       )
                       ''')

        # 7. AI 任务表 (增加 strictness 和 extra_desc 字段)
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS ai_tasks
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           name          TEXT,
                           status        TEXT,
                           grader_id     TEXT,
                           log_info      TEXT,
                           exam_path     TEXT,
                           standard_path TEXT,
                           strictness    TEXT      DEFAULT 'standard',
                           extra_desc    TEXT,
                           max_score     INTEGER   DEFAULT 100, -- 新增字段
                           created_by    INTEGER   DEFAULT 1,
                           created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS grader_recycle_bin
                       (
                           id              INTEGER PRIMARY KEY AUTOINCREMENT,
                           grader_id       TEXT,
                           original_name   TEXT,
                           backup_filename TEXT,
                           deleted_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS file_assets
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           file_hash     TEXT UNIQUE NOT NULL, -- SHA256 哈希值
                           original_name TEXT,                 -- 首次上传时的文件名
                           file_size     INTEGER,              -- 字节数
                           physical_path TEXT,                 -- 磁盘物理路径
                           parsed_content TEXT,                -- 存储AI解析后的纯文本/结构化数据
                           meta_info   TEXT,                 -- 存储文件的元信息，如页数、作者等（JSON格式）
                           version       INTEGER   DEFAULT 1,  -- 版本号，便于未来扩展
                           doc_category  TEXT    DEFAULT 'exam', -- 文档类别，如 exam, course_material 等
                           academic_year TEXT,                 -- 学年，如 2023-2024
                           semester      TEXT,                 -- 学期，如 Fall, Spring
                           course_name   TEXT,                 -- 课程名称
                           cohort_tag    TEXT,                 -- 批次标签，如 2401, 240
                           uploaded_by   INTEGER,              -- 上传者ID
                           created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')

        # 8. 签名集表 [NEW]
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS signatures
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           name
                           TEXT
                           NOT
                           NULL,    -- 签名名称 (如: 张三-楷体)
                           file_hash
                           TEXT
                           NOT
                           NULL,    -- 文件哈希 (去重)
                           file_path
                           TEXT
                           NOT
                           NULL,    -- 物理存储路径
                           uploaded_by
                           INTEGER, -- 上传者ID
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        # [NEW] 1. 新增导出模板表
        # 该表存储模板的元数据和前端所需的表单定义(Schema)，实现UI解耦
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS export_templates
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           template_id
                           TEXT
                           UNIQUE
                           NOT
                           NULL, -- 对应 Python 类中的 ID
                           name
                           TEXT
                           NOT
                           NULL, -- 显示名称
                           description
                           TEXT,
                           file_path
                           TEXT, -- 物理 py 文件路径
                           ui_schema
                           TEXT, -- JSON 格式的前端表单配置
                           is_active
                           BOOLEAN
                           DEFAULT
                           1,
                           updated_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_capability ON ai_models (capability)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_hash ON file_assets (file_hash)')

        conn.commit()
        self._init_super_admin(cursor, conn)

        self._migrate_table(cursor, conn, "classes", "created_by", "INTEGER DEFAULT 1")
        self._migrate_table(cursor, conn, "ai_tasks", "created_by", "INTEGER DEFAULT 1")
        self._migrate_table(cursor, conn, "ai_tasks", "exam_path", "TEXT")  # 之前已有的迁移
        self._migrate_table(cursor, conn, "ai_tasks", "standard_path", "TEXT")
        self._migrate_table(cursor, conn, "ai_tasks", "strictness", "TEXT DEFAULT 'standard'")
        self._migrate_table(cursor, conn, "ai_tasks", "extra_desc", "TEXT DEFAULT ''")
        self._migrate_table(cursor, conn, "ai_tasks", "max_score", "INTEGER DEFAULT 100")
        self._migrate_table(cursor, conn, "users", "has_seen_help", "BOOLEAN DEFAULT 0")
        self._migrate_table(cursor, conn, "file_assets", "parsed_content", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "meta_info", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "version", "INTEGER DEFAULT 1")
        self._migrate_table(cursor, conn, "file_assets", "doc_category", "TEXT DEFAULT 'exam'")
        self._migrate_table(cursor, conn, "file_assets", "academic_year", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "semester", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "course_name", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "cohort_tag", "TEXT")  # 关键：用于区分 2401 和 2406

    def _migrate_table(self, cursor, conn, table, column, type_def):
        """辅助函数：检查列是否存在，不存在则添加"""
        try:
            cursor.execute(f"SELECT {column} FROM {table} LIMIT 1")
        except sqlite3.OperationalError:
            print(f"[DB] Migrating {table} table (Adding {column})...")
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
                conn.commit()
            except Exception as e:
                print(f"[DB] Migration failed for {column}: {e}")

    def _init_super_admin(self, cursor, conn):
        admin_user = Config.ADMIN_USERNAME
        cursor.execute('SELECT id FROM users WHERE username = ?', (admin_user,))
        if not cursor.fetchone():
            pwd_hash = generate_password_hash(Config.ADMIN_PASSWORD)
            cursor.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)',
                           (admin_user, pwd_hash))
            conn.commit()
            print(f"[DB] 超级管理员已初始化: {admin_user}")

    def get_document_library_tree(self, user_id):
        """
        获取文档库的目录树结构：学年 -> 学期 -> 课程 -> 适用人群
        """
        conn = self.get_connection()
        # 聚合查询，找出所有存在的组合
        sql = '''
              SELECT DISTINCT academic_year, \
                              semester, \
                              course_name, \
                              cohort_tag
              FROM file_assets
              WHERE uploaded_by = ? \
                AND academic_year IS NOT NULL
              ORDER BY academic_year DESC, semester ASC, course_name \
              '''
        return [dict(row) for row in conn.execute(sql, (user_id,)).fetchall()]

    def get_files_by_filter(self, user_id, doc_category=None, year=None, course=None, cohort=None, search=None):
        """
        [增强版] 高级筛选接口
        """
        conn = self.get_connection()
        sql = "SELECT f.*, u.username as uploader_name FROM file_assets f LEFT JOIN users u ON f.uploaded_by = u.id WHERE f.parsed_content IS NOT NULL"
        params = []

        # 权限控制：只能看自己的，或者管理员看全部 (根据业务需求调整，这里暂时只查自己的)
        # 如果需要看全部，请移除下面这行或根据 user_id 逻辑调整
        sql += " AND f.uploaded_by = ?"
        params.append(user_id)

        if doc_category:
            sql += " AND f.doc_category = ?"
            params.append(doc_category)
        if year:
            sql += " AND f.academic_year = ?"
            params.append(year)
        if course:
            sql += " AND f.course_name = ?"
            params.append(course)
        if cohort:
            sql += " AND f.cohort_tag = ?"
            params.append(cohort)

        # [新增] 模糊搜索
        if search:
            sql += " AND f.original_name LIKE ?"
            params.append(f"%{search}%")

        sql += " ORDER BY f.created_at DESC"
        return [dict(row) for row in conn.execute(sql, params).fetchall()]

    # ================= 签名集管理 [NEW] =================
    def add_signature(self, name, file_hash, file_path, user_id):
        conn = self.get_connection()
        conn.execute("INSERT INTO signatures (name, file_hash, file_path, uploaded_by) VALUES (?, ?, ?, ?)",
                     (name, file_hash, file_path, user_id))
        conn.commit()

    def get_signatures(self, search=None, user_id=None):
        conn = self.get_connection()
        sql = '''
              SELECT s.*, u.username as uploader_name
              FROM signatures s
                       LEFT JOIN users u ON s.uploaded_by = u.id
              WHERE 1 = 1
              '''
        params = []
        if search:
            sql += " AND s.name LIKE ?"
            params.append(f"%{search}%")

        sql += " ORDER BY s.created_at DESC"
        return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def get_signature_by_id(self, sig_id):
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM signatures WHERE id=?", (sig_id,)).fetchone()
        return dict(row) if row else None

    def get_signature_usage_count(self, file_hash):
        """检查物理文件被引用的次数"""
        conn = self.get_connection()
        row = conn.execute("SELECT COUNT(*) as cnt FROM signatures WHERE file_hash=?", (file_hash,)).fetchone()
        return row['cnt']

    def delete_signature(self, sig_id):
        conn = self.get_connection()
        conn.execute("DELETE FROM signatures WHERE id=?", (sig_id,)).commit()

    def update_ai_task_status(self, task_id, status):
        conn = self.get_connection()
        conn.execute("UPDATE ai_tasks SET status=? WHERE id=?", (status, task_id))
        conn.commit()

    # [新增] 更新文件的解析内容
    def update_file_parsed_content(self, file_id, content):
        conn = self.get_connection()
        conn.execute("UPDATE file_assets SET parsed_content = ? WHERE id = ?", (content, file_id))
        conn.commit()

    # [新增] 添加标记帮助已读的方法
    def mark_help_read(self, user_id):
        conn = self.get_connection()
        conn.execute("UPDATE users SET has_seen_help = 1 WHERE id = ?", (user_id,))
        conn.commit()
        return True

    def login_simple_user(self, username):
        """普通用户登录：如果不存在则自动注册"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 查询用户
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user:
            return dict(user)
        else:
            # 自动注册
            cursor.execute('INSERT INTO users (username, is_admin) VALUES (?, 0)', (username,))
            conn.commit()
            user_id = cursor.lastrowid
            return {"id": user_id, "username": username, "is_admin": 0}

    # ================= 管理员相关 =================
    def verify_admin_login(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND is_admin = 1', (username,))
        user = cursor.fetchone()
        if user and user['password_hash'] and check_password_hash(user['password_hash'], password):
            return dict(user)
        return None

    def get_file_by_hash(self, file_hash):
        """根据哈希获取文件记录"""
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM file_assets WHERE file_hash=?", (file_hash,)).fetchone()
        return dict(row) if row else None

    def get_file_by_id(self, file_id):
        """根据ID获取文件记录"""
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM file_assets WHERE id=?", (file_id,)).fetchone()
        return dict(row) if row else None

    # ================= [新增] 文件资产管理逻辑 =================
    def save_file_asset(self, file_hash, original_name, file_size, physical_path, user_id):
        """保存新的文件资产记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                           INSERT INTO file_assets (file_hash, original_name, file_size, physical_path, uploaded_by)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (file_hash, original_name, file_size, physical_path, user_id))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # 如果哈希冲突（极低概率并发导致），返回已存在的 ID
            row = conn.execute("SELECT id FROM file_assets WHERE file_hash=?", (file_hash,)).fetchone()
            return row['id'] if row else None

    def get_user_recent_files(self, user_id, limit=20, search_name=None):
        """获取用户最近使用的文件，支持搜索"""
        conn = self.get_connection()
        sql = "SELECT * FROM file_assets WHERE uploaded_by=? "
        params = [user_id]

        if search_name:
            sql += " AND original_name LIKE ? "
            params.append(f"%{search_name}%")

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def get_files(self, limit=50, search_name=None):
        """获取所有文件，支持搜索"""
        conn = self.get_connection()
        sql = "SELECT * FROM file_assets WHERE 1=1 "
        params = []

        if search_name:
            sql += " AND original_name LIKE ? "
            params.append(f"%{search_name}%")

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def get_user_parsed_files(self, user_id):
        """获取已解析的文件（附带作者信息）"""
        conn = self.get_connection()
        sql = '''
              SELECT file_assets.*, users.username AS uploader_name
              FROM file_assets
              LEFT JOIN users ON file_assets.uploaded_by = users.id
              WHERE parsed_content IS NOT NULL
              ORDER BY created_at DESC
              '''
        return [dict(row) for row in conn.execute(sql).fetchall()]

    def delete_file_asset(self, file_id):
        """删除文件资产记录"""
        conn = self.get_connection()
        conn.execute("DELETE FROM file_assets WHERE id=?", (file_id,))
        conn.commit()


    # ================= AI 配置相关 (Admin用) =================
    def get_all_providers(self):
        conn = self.get_connection()
        return [dict(row) for row in conn.execute('SELECT * FROM ai_providers').fetchall()]

    def get_models_by_provider(self, p_id):
        conn = self.get_connection()
        return [dict(row) for row in conn.execute('SELECT * FROM ai_models WHERE provider_id=?', (p_id,)).fetchall()]

    # --- AI Admin CRUD (简化版，保留核心) ---
    def add_provider(self, name, provider_type, api_key, base_url=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO ai_providers (name, provider_type, base_url, api_key) VALUES (?, ?, ?, ?)',
                       (name, provider_type, base_url, api_key))
        conn.commit()
        return cursor.lastrowid

    def update_provider(self, p_id, name, api_key, base_url, max_conn):
        conn = self.get_connection()
        conn.execute('UPDATE ai_providers SET name=?, api_key=?, base_url=?, max_concurrent_requests=? WHERE id=?',
                     (name, api_key, base_url, max_conn, p_id))
        conn.commit()
        return True

    def delete_provider(self, p_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM ai_models WHERE provider_id=?', (p_id,))
        conn.execute('DELETE FROM ai_providers WHERE id=?', (p_id,))
        conn.commit()
        return True

    def toggle_provider(self, p_id, state):
        conn = self.get_connection()
        conn.execute('UPDATE ai_providers SET is_enabled=? WHERE id=?', (1 if state else 0, p_id))
        conn.commit()

    def get_all_providers(self):
        conn = self.get_connection()
        return [dict(row) for row in conn.execute('SELECT * FROM ai_providers').fetchall()]

    def get_models_by_provider(self, p_id):
        conn = self.get_connection()
        return [dict(row) for row in conn.execute('SELECT * FROM ai_models WHERE provider_id=?', (p_id,)).fetchall()]

    def add_model(self, p_id, name, capability, weight=50):
        conn = self.get_connection()
        conn.execute('INSERT INTO ai_models (provider_id, model_name, capability, weight) VALUES (?, ?, ?, ?)',
                     (p_id, name, capability, weight))
        conn.commit()

    def update_model(self, m_id, name, capability, weight, force_json):
        conn = self.get_connection()
        conn.execute('UPDATE ai_models SET model_name=?, capability=?, weight=?, can_force_json=? WHERE id=?',
                     (name, capability, weight, 1 if force_json else 0, m_id))
        conn.commit()
        return True

    def delete_model(self, m_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM ai_models WHERE id=?', (m_id,))
        conn.commit()

    def toggle_model(self, m_id, state):
        conn = self.get_connection()
        conn.execute('UPDATE ai_models SET is_enabled=? WHERE id=?', (1 if state else 0, m_id))
        conn.commit()

    # ================= AI 服务调用相关 =================
    def get_best_ai_config(self, capability):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = '''
                SELECT p.id   as provider_id, \
                       p.name as provider_name, \
                       p.provider_type,
                       p.base_url, \
                       p.api_key, \
                       p.max_concurrent_requests, \
                       m.model_name
                FROM ai_models m
                         JOIN ai_providers p ON m.provider_id = p.id
                WHERE m.capability = ? \
                  AND m.is_enabled = 1 \
                  AND p.is_enabled = 1
                ORDER BY m.weight DESC \
                LIMIT 1 \
                '''
        cursor.execute(query, (capability,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ================= 批改系统业务逻辑 (将 app.py 的 SQL 移到这里) =================

    def get_classes(self, user_id=None):
        """只获取当前用户创建的班级"""
        conn = self.get_connection()
        if user_id:
            return [dict(row) for row in
                    conn.execute("SELECT * FROM classes WHERE created_by=? ORDER BY id DESC", (user_id,)).fetchall()]
        return [dict(row) for row in conn.execute("SELECT * FROM classes ORDER BY id DESC").fetchall()]

    def get_class_by_id(self, class_id):
        conn = self.get_connection()
        # 这里为了安全，其实应该校验 user_id，但为了简化，暂只在前端做隔离，后端通过 ID 获取
        row = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
        return dict(row) if row else None

    def create_class(self, name, course, strategy, user_id, workspace_path=""):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO classes (name, course, workspace_path, strategy, created_by) VALUES (?, ?, ?, ?, ?)",
                    (name, course, workspace_path, strategy, user_id))
        conn.commit()
        return cur.lastrowid

    def delete_class(self, class_id):
        conn = self.get_connection()
        conn.execute("DELETE FROM students WHERE class_id=?", (class_id,))
        conn.execute("DELETE FROM grades WHERE class_id=?", (class_id,))
        conn.execute("DELETE FROM classes WHERE id=?", (class_id,))
        conn.commit()

    def update_class_workspace(self, class_id, workspace_path):
        conn = self.get_connection()
        conn.execute("UPDATE classes SET workspace_path = ? WHERE id = ?", (workspace_path, class_id))
        conn.commit()

    def add_student(self, student_id, name, class_id):
        conn = self.get_connection()
        conn.execute("INSERT INTO students (student_id, name, class_id) VALUES (?, ?, ?)",
                     (student_id, name, class_id))
        conn.commit()

    def get_students_with_grades(self, class_id):
        conn = self.get_connection()
        # 移除 task1_score, task2_score，改为 score_details
        sql = '''
              SELECT s.*,
                     g.total_score,
                     g.score_details,
                     g.deduct_details,
                     g.status,
                     g.filename
              FROM students s
                       LEFT JOIN grades g ON s.student_id = g.student_id AND g.class_id = s.class_id
              WHERE s.class_id = ? \
              '''
        return [dict(row) for row in conn.execute(sql, (class_id,)).fetchall()]

    def get_student_detail(self, class_id, student_id):
        conn = self.get_connection()
        sql = '''
              SELECT s.*, \
                     g.total_score,
                     g.score_details, \
                     g.deduct_details, \
                     g.status, \
                     g.filename
              FROM students s
                       LEFT JOIN grades g ON s.student_id = g.student_id AND g.class_id = s.class_id
              WHERE s.student_id = ? \
                AND s.class_id = ? \
              '''
        row = conn.execute(sql, (student_id, class_id)).fetchone()
        return dict(row) if row else None

    def clear_grades(self, class_id):
        conn = self.get_connection()
        conn.execute("DELETE FROM grades WHERE class_id=?", (class_id,))
        conn.commit()

    def save_grade(self, student_id, class_id, total, score_details_json, deduct_details, status, filename):
        conn = self.get_connection()
        # 使用 REPLACE INTO 或先删后插 (这里保持原有逻辑，先删后插)
        conn.execute("DELETE FROM grades WHERE student_id=? AND class_id=?", (student_id, class_id))

        conn.execute('''
                     INSERT INTO grades (student_id, class_id, total_score, score_details,
                                         deduct_details, status, filename)
                     VALUES (?, ?, ?, ?, ?, ?, ?)
                     ''', (student_id, class_id, total, score_details_json, deduct_details, status, filename))
        conn.commit()

    def save_grade_error(self, student_id, class_id, msg, filename):
        conn = self.get_connection()
        conn.execute("DELETE FROM grades WHERE student_id=? AND class_id=?", (student_id, class_id))

        # 错误时，score_details 存为空列表 JSON
        conn.execute('''
                     INSERT INTO grades (student_id, class_id, total_score, score_details,
                                         deduct_details, status, filename)
                     VALUES (?, ?, 0, '[]', ?, "ERROR", ?)
                     ''', (student_id, class_id, msg, filename))
        conn.commit()

    # ================= AI 任务相关 =================
    def insert_ai_task(self, name, status="pending", log_info="等待队列中...",
                       exam_path=None, standard_path=None,
                       strictness='standard', extra_desc='', max_score=100, user_id=1, grader_id=None):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO ai_tasks (name, status, log_info, exam_path, standard_path, strictness, extra_desc, max_score, created_by, grader_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, status, log_info, exam_path, standard_path, strictness, extra_desc, max_score, user_id, grader_id)
        )
        conn.commit()
        return cur.lastrowid

    def update_ai_task(self, task_id, status=None, log_info=None, grader_id=None):
        conn = self.get_connection()
        updates = []
        params = []
        if status:
            updates.append("status=?")
            params.append(status)
        if log_info:
            updates.append("log_info=?")
            params.append(log_info)
        if grader_id:
            updates.append("grader_id=?")
            params.append(grader_id)

        if updates:
            params.append(task_id)
            conn.execute(f"UPDATE ai_tasks SET {', '.join(updates)} WHERE id=?", params)
            conn.commit()

    def update_task_status_by_grader_id(self, grader_id, status):
        """[新增] 根据 grader_id 更新任务状态 (用于删除/恢复同步)"""
        conn = self.get_connection()
        conn.execute("UPDATE ai_tasks SET status=? WHERE grader_id=?", (status, grader_id))
        conn.commit()

    def get_ai_tasks(self, limit=20):
        """获取任务，并联表查询创建者名称"""
        conn = self.get_connection()
        sql = '''
              SELECT t.*, u.username as creator_name
              FROM ai_tasks t
                       LEFT JOIN users u ON t.created_by = u.id
              ORDER BY t.created_at DESC \
              LIMIT ? \
              '''
        return [dict(row) for row in conn.execute(sql, (limit,)).fetchall()]

    def get_ai_task_by_id(self, task_id):
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM ai_tasks WHERE id=?", (task_id,)).fetchone()
        return dict(row) if row else None

    def get_task_by_grader_id(self, grader_id):
        conn = self.get_connection()
        # 联表查询获取创建者
        sql = '''
              SELECT t.*, u.username as creator_name, u.id as creator_id
              FROM ai_tasks t
                       LEFT JOIN users u ON t.created_by = u.id
              WHERE t.grader_id = ?
              ORDER BY t.created_at DESC \
              LIMIT 1 \
              '''
        row = conn.execute(sql, (grader_id,)).fetchone()
        return dict(row) if row else None

    # --- 回收站逻辑 ---

    def recycle_grader_record(self, grader_id, original_name, backup_filename):
        conn = self.get_connection()
        conn.execute("INSERT INTO grader_recycle_bin (grader_id, original_name, backup_filename) VALUES (?, ?, ?)",
                     (grader_id, original_name, backup_filename))
        conn.commit()

    def get_recycled_graders(self):
        conn = self.get_connection()
        return [dict(row) for row in
                conn.execute("SELECT * FROM grader_recycle_bin ORDER BY deleted_at DESC").fetchall()]

    def restore_grader_record(self, recycle_id):
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM grader_recycle_bin WHERE id=?", (recycle_id,)).fetchone()
        if row:
            conn.execute("DELETE FROM grader_recycle_bin WHERE id=?", (recycle_id,)).commit()
            return dict(row)
        return None
