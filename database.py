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
                           course_name   TEXT      DEFAULT '',
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

        # [NEW] 9. 学生名单表
        # 存储解析后的学生名单记录和元数据
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS student_lists
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           file_asset_id INTEGER,           -- 关联的文件资产ID
                           class_name   TEXT,              -- 班级名称
                           college      TEXT,              -- 学院
                           department   TEXT,              -- 系部
                           enrollment_year TEXT,           -- 入学年份
                           education_type TEXT,            -- 培养类型 (普本/专升本/专科)
                           student_count  INTEGER DEFAULT 0, -- 学生数量
                           has_gender     BOOLEAN DEFAULT 0, -- 是否包含性别信息
                           uploaded_by   INTEGER,          -- 上传者ID
                           created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')

        # [NEW] 10. 学生详细信息表
        # 存储每个学生的详细信息
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS student_details
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           student_list_id INTEGER,        -- 关联的学生名单ID
                           student_id    TEXT,             -- 学号
                           name          TEXT,             -- 姓名
                           gender        TEXT,             -- 性别
                           email         TEXT,             -- 邮箱
                           phone         TEXT,             -- 电话
                           status        TEXT DEFAULT 'normal', -- 状态 (normal/abnormal)
                           created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           UNIQUE(student_list_id, student_id)
                       )
                       ''')

        # 11. 教务系统账号绑定表 [NEW]
        # 用于存储用户的教务系统账号，以便下次自动登录
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS jwxt_bindings
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           user_id       INTEGER NOT NULL UNIQUE,
                           jwxt_username TEXT    NOT NULL,
                           jwxt_password TEXT    NOT NULL, -- 实际生产中建议使用 AES 加密存储
                           cookies       TEXT,             -- 预留：存储 Session Cookies 缓存
                           is_active     BOOLEAN   DEFAULT 1,
                           last_check_at TIMESTAMP,
                           created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                       )
                       ''')

        # 12. 通知表 [NEW]
        # 用于存储系统通知、任务状态更新等消息
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS notifications
                       (
                           id            INTEGER PRIMARY KEY AUTOINCREMENT,
                           user_id       INTEGER NOT NULL,            -- 接收通知的用户
                           type          TEXT    NOT NULL,            -- 通知类型: task_pending, task_processing, task_success, task_failed, system
                           title         TEXT    NOT NULL,            -- 通知标题
                           message       TEXT,                        -- 通知内容
                           detail        TEXT,                        -- 详细信息
                           link          TEXT,                        -- 相关链接
                           related_id    TEXT,                        -- 关联的实体 ID (如 task_id, grader_id)
                           is_read       BOOLEAN   DEFAULT 0,         -- 是否已读
                           created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                       )
                       ''')

        # 13. AI 欢迎语缓存表 [NEW]
        # 用于存储 AI 生成的欢迎语，带 TTL 缓存
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS ai_welcome_messages
                       (
                           id               INTEGER PRIMARY KEY AUTOINCREMENT,
                           user_id          INTEGER NOT NULL,
                           page_context     TEXT    NOT NULL,        -- 页面上下文: dashboard, tasks, student_list, ai_generator, export
                           message_content  TEXT    NOT NULL,        -- AI 生成的欢迎语文本
                           created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           expires_at       TIMESTAMP NOT NULL,        -- 缓存过期时间
                           context_snapshot TEXT,                       -- 生成时的上下文快照 (JSON格式，用于调试)
                           last_request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                       )
                       ''')

        # 14. AI 对话会话表 [NEW]
        # 用于存储用户与 AI 助手的对话会话
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS ai_conversations
                       (
                           id              INTEGER PRIMARY KEY AUTOINCREMENT,
                           user_id         INTEGER NOT NULL,
                           title           TEXT DEFAULT '新对话',
                           status          TEXT DEFAULT 'active',  -- active, archived
                           created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           last_active_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                       )
                       ''')

        # 15. AI 对话消息表 [NEW]
        # 用于存储对话中的每条消息
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS ai_messages
                       (
                           id              INTEGER PRIMARY KEY AUTOINCREMENT,
                           conversation_id INTEGER NOT NULL,
                           role            TEXT NOT NULL,           -- user, assistant, system
                           content         TEXT NOT NULL,
                           trigger_type    TEXT DEFAULT 'user_message',  -- user_message, page_change, operation_complete, system
                           metadata_json   TEXT,                    -- 扩展元数据 (page_context, operation_type 等)
                           created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id) ON DELETE CASCADE
                       )
                       ''')

        # 16. AI 速率限制表 [NEW]
        # 用于控制主动触发的频率限制
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS ai_rate_limits
                       (
                           user_id                 INTEGER PRIMARY KEY,
                           last_proactive_trigger  TIMESTAMP NOT NULL,
                           updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                       )
                       ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_capability ON ai_models (capability)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_hash ON file_assets (file_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_user ON notifications (user_id, is_read)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_related ON notifications (related_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_welcome_user_page ON ai_welcome_messages(user_id, page_context)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_welcome_expires ON ai_welcome_messages(expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_user ON ai_conversations(user_id, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_conversation ON ai_messages(conversation_id, created_at)')

        conn.commit()
        self._init_super_admin(cursor, conn)

        self._migrate_table(cursor, conn, "classes", "created_by", "INTEGER DEFAULT 1")
        self._migrate_table(cursor, conn, "ai_tasks", "created_by", "INTEGER DEFAULT 1")
        self._migrate_table(cursor, conn, "ai_tasks", "exam_path", "TEXT")  # 之前已有的迁移
        self._migrate_table(cursor, conn, "ai_tasks", "standard_path", "TEXT")
        self._migrate_table(cursor, conn, "ai_tasks", "strictness", "TEXT DEFAULT 'standard'")
        self._migrate_table(cursor, conn, "ai_tasks", "extra_desc", "TEXT DEFAULT ''")
        self._migrate_table(cursor, conn, "ai_tasks", "max_score", "INTEGER DEFAULT 100")
        self._migrate_table(cursor, conn, "ai_tasks", "course_name", "TEXT DEFAULT ''")
        self._migrate_table(cursor, conn, "users", "has_seen_help", "BOOLEAN DEFAULT 0")
        self._migrate_table(cursor, conn, "file_assets", "parsed_content", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "meta_info", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "version", "INTEGER DEFAULT 1")
        self._migrate_table(cursor, conn, "file_assets", "doc_category", "TEXT DEFAULT 'exam'")
        self._migrate_table(cursor, conn, "file_assets", "academic_year", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "semester", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "course_name", "TEXT")
        self._migrate_table(cursor, conn, "file_assets", "cohort_tag", "TEXT")  # 关键：用于区分 2401 和 2406
        self._migrate_table(cursor, conn, "ai_welcome_messages", "last_request_time", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

        # 学生名单表迁移
        self._migrate_table(cursor, conn, "student_lists", "department", "TEXT")

        # 学生详细信息表迁移（如果表已存在但缺少字段）
        self._migrate_table(cursor, conn, "student_details", "status", "TEXT DEFAULT 'normal'")

        # 教务系统绑定表迁移
        self._migrate_table(cursor, conn, "jwxt_bindings", "cookies", "TEXT")

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

    def get_document_library_tree(self, user_id, is_admin=False):
        """
        获取文档库的目录树结构：学年 -> 学期 -> 课程 -> 适用人群
        优化：即使 academic_year 为空，也根据 course_name 分组
        注意：文档库为共享设计，所有用户可见所有分类
        """
        conn = self.get_connection()
        # 文档库共享设计：所有人可见所有文档分类
        sql = '''
              SELECT DISTINCT
                  COALESCE(academic_year, '未分类') as academic_year,
                  semester,
                  course_name,
                  cohort_tag
              FROM file_assets
              WHERE course_name IS NOT NULL AND course_name != ''
              ORDER BY academic_year DESC, semester ASC, course_name
              '''
        return [dict(row) for row in conn.execute(sql).fetchall()]

    def get_files_by_filter(self, user_id, doc_category=None, year=None, course=None, cohort=None, search=None, is_admin=False, include_unparsed=False):
        """
        [增强版] 高级筛选接口
        :param include_unparsed: 是否包含未解析的文件
        注意：文档库为共享设计，所有用户可见所有文档（编辑/删除权限在前端按 is_owner 控制）
        """
        conn = self.get_connection()
        # 文档库共享设计：所有人可见所有文档
        sql = "SELECT f.*, u.username as uploader_name FROM file_assets f LEFT JOIN users u ON f.uploaded_by = u.id WHERE 1=1"
        params = []

        # 注意：已移除权限控制，文档库对所有用户可见
        # 编辑/删除权限通过前端 is_owner 字段控制

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

        # [增强] 模糊搜索：支持文件名和内容搜索
        if search:
            sql += " AND (f.original_name LIKE ? OR f.parsed_content LIKE ? OR f.course_name LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])

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

    # [新增] 更新文件的元数据信息
    def update_file_metadata(self, file_id, meta_info, doc_category=None, course_name=None, academic_year=None):
        """
        更新文件的元数据
        :param file_id: 文件 ID
        :param meta_info: JSON 字符串或字典
        :param doc_category: 文档类别 (可选更新)
        :param course_name: 课程名称 (可选更新)
        :param academic_year: 学年 (可选更新)
        """
        import json
        conn = self.get_connection()

        # 构建动态 SQL
        updates = ["meta_info = ?"]
        params = [json.dumps(meta_info, ensure_ascii=False) if isinstance(meta_info, dict) else meta_info]

        if doc_category is not None:
            updates.append("doc_category = ?")
            params.append(doc_category)
        if course_name is not None:
            updates.append("course_name = ?")
            params.append(course_name)
        if academic_year is not None:
            updates.append("academic_year = ?")
            params.append(academic_year)

        params.append(file_id)
        sql = f"UPDATE file_assets SET {', '.join(updates)} WHERE id = ?"
        conn.execute(sql, params)
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
                       strictness='standard', extra_desc='', max_score=100, user_id=1, grader_id=None, course_name=None):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO ai_tasks (name, status, log_info, exam_path, standard_path, strictness, extra_desc, max_score, created_by, grader_id, course_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, status, log_info, exam_path, standard_path, strictness, extra_desc, max_score, user_id, grader_id, course_name)
        )
        conn.commit()
        return cur.lastrowid

    def update_ai_task(self, task_id, status=None, log_info=None, grader_id=None, course_name=None):
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

        if course_name:
            updates.append("course_name=?")
            params.append(course_name)

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

    # ================= 学生名单管理 =================

    def save_student_list(self, file_asset_id, class_name, college, department, enrollment_year,
                         education_type, student_count, has_gender, user_id):
        """保存学生名单记录"""
        import json
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO student_lists (file_asset_id, class_name, college, department, enrollment_year,
                                      education_type, student_count, has_gender, uploaded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_asset_id, class_name, college, department, enrollment_year,
                 education_type, student_count, has_gender, user_id))
        conn.commit()

        list_id = cursor.lastrowid

        # 同时更新 file_assets 表，将文档类别设置为 "other"
        # 并更新元数据
        meta_info = {
            "class_name": class_name,
            "college": college,
            "department": department,
            "enrollment_year": enrollment_year,
            "education_type": education_type,
            "student_count": student_count,
            "has_gender": has_gender
        }
        conn.execute('''
            UPDATE file_assets
            SET doc_category = 'other',
                meta_info = ?
            WHERE id = ?
            ''', (json.dumps(meta_info, ensure_ascii=False), file_asset_id))
        conn.commit()

        return list_id

    def add_student_detail(self, student_list_id, student_id, name, gender='', email='', phone=''):
        """添加学生详细信息"""
        conn = self.get_connection()
        try:
            conn.execute('''
                INSERT INTO student_details (student_list_id, student_id, name, gender, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (student_list_id, student_id, name, gender, email, phone))
            conn.commit()
            return True
        except:
            return False

    def get_student_details(self, student_list_id):
        """获取学生名单的所有学生详细信息"""
        conn = self.get_connection()
        rows = conn.execute('''
            SELECT * FROM student_details
            WHERE student_list_id = ?
            ORDER BY student_id
            ''', (student_list_id,)).fetchall()
        return [dict(row) for row in rows]

    def update_student_detail(self, detail_id, student_id, name, gender, email, phone, status):
        """更新学生详细信息"""
        conn = self.get_connection()
        conn.execute('''
            UPDATE student_details
            SET student_id = ?, name = ?, gender = ?, email = ?, phone = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (student_id, name, gender, email, phone, status, detail_id))
        conn.commit()

    def delete_student_detail(self, detail_id):
        """删除学生详细信息"""
        conn = self.get_connection()
        conn.execute("DELETE FROM student_details WHERE id=?", (detail_id,))
        conn.commit()

    def update_student_list_metadata(self, list_id, class_name, college, department, enrollment_year, education_type):
        """更新学生名单元数据"""
        conn = self.get_connection()
        conn.execute('''
            UPDATE student_lists
            SET class_name = ?, college = ?, department = ?, enrollment_year = ?, education_type = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (class_name, college, department, enrollment_year, education_type, list_id))
        conn.commit()

        # 同步更新 file_assets 的元数据
        sl = conn.execute("SELECT * FROM student_lists WHERE id=?", (list_id,)).fetchone()
        if sl:
            import json
            meta_info = {
                "class_name": sl['class_name'],
                "college": sl['college'],
                "department": sl['department'],
                "enrollment_year": str(sl['enrollment_year']) if sl['enrollment_year'] else '',
                "education_type": sl['education_type'],
                "student_count": sl['student_count'],
                "has_gender": sl['has_gender']
            }
            conn.execute('''
                UPDATE file_assets
                SET meta_info = ?
                WHERE id = ?
                ''', (json.dumps(meta_info, ensure_ascii=False), sl['file_asset_id']))
            conn.commit()

    def get_student_list_by_file_id(self, file_asset_id):
        """根据文件ID获取学生名单记录"""
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM student_lists WHERE file_asset_id=?", (file_asset_id,)).fetchone()
        return dict(row) if row else None

        # 在 database.py 中找到 get_student_lists 方法并替换为：

    def get_student_lists(self, user_id=None, fetch_all=False, search=None):
        """
        获取学生名单列表
        :param user_id: 当前用户ID
        :param fetch_all: 是否获取所有数据 (权限: 普通用户可使用任何人的数据 -> True)
        :param search: 模糊搜索关键词 (班级名/学院/年份)
        """
        conn = self.get_connection()

        sql = '''
              SELECT sl.*, u.username as uploader_name, fa.original_name as source_file
              FROM student_lists sl
                       LEFT JOIN users u ON sl.uploaded_by = u.id
                       LEFT JOIN file_assets fa ON sl.file_asset_id = fa.id
              WHERE 1 = 1
              '''
        params = []

        # 1. 权限控制逻辑
        # 如果不是获取全部 (fetch_all=False) 且指定了 user_id，则只看自己的
        # 如果是 fetch_all=True，则忽略 user_id 限制，返回所有 (符合"使用任何人的数据"需求)
        if user_id and not fetch_all:
            sql += " AND sl.uploaded_by = ?"
            params.append(user_id)

        # 2. 搜索逻辑 (新增)
        if search:
            sql += " AND (sl.class_name LIKE ? OR sl.college LIKE ? OR sl.enrollment_year LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        sql += " ORDER BY sl.created_at DESC"

        return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def delete_student_list(self, list_id):
        """删除学生名单记录及所有关联的学生"""
        conn = self.get_connection()
        # 先删除所有关联的学生详情
        conn.execute("DELETE FROM student_details WHERE student_list_id=?", (list_id,))
        # 再删除学生名单记录
        conn.execute("DELETE FROM student_lists WHERE id=?", (list_id,))
        conn.commit()

    def get_user_by_id(self, user_id):
        """根据用户ID获取用户信息"""
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def save_jwxt_binding(self, user_id, username, password):
        """保存或更新教务系统绑定信息"""
        conn = self.get_connection()
        # 使用 INSERT OR REPLACE 或先删后插确保唯一性
        conn.execute("DELETE FROM jwxt_bindings WHERE user_id=?", (user_id,))
        conn.execute('''
                     INSERT INTO jwxt_bindings (user_id, jwxt_username, jwxt_password, is_active, last_check_at)
                     VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                     ''', (user_id, username, password))
        conn.commit()

    def get_jwxt_binding(self, user_id, only_active=False):
        """
        获取用户的教务绑定信息
        :param user_id: 用户ID
        :param only_active: 是否只获取激活状态的绑定
        """
        conn = self.get_connection()
        if only_active:
            row = conn.execute(
                "SELECT * FROM jwxt_bindings WHERE user_id=? AND is_active=1",
                (user_id,)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM jwxt_bindings WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def update_jwxt_binding_status(self, user_id, is_active):
        """更新教务绑定的激活状态"""
        conn = self.get_connection()
        conn.execute('''
            UPDATE jwxt_bindings SET is_active = ?, last_check_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (1 if is_active else 0, user_id))
        conn.commit()

    def update_jwxt_last_check(self, user_id):
        """更新最后检查时间"""
        conn = self.get_connection()
        conn.execute('''
            UPDATE jwxt_bindings SET last_check_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

    def delete_jwxt_binding(self, user_id):
        """解除绑定"""
        conn = self.get_connection()
        conn.execute("DELETE FROM jwxt_bindings WHERE user_id=?", (user_id,))
        conn.commit()

    # ================= 通知管理 [NEW] =================

    def create_notification(self, user_id, notif_type, title, message=None, detail=None, link=None, related_id=None):
        """
        创建一条通知
        :param user_id: 接收通知的用户 ID
        :param notif_type: 通知类型 (task_pending, task_processing, task_success, task_failed, system)
        :param title: 通知标题
        :param message: 通知内容
        :param detail: 详细信息
        :param link: 相关链接
        :param related_id: 关联的实体 ID
        :return: 新创建的通知 ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, type, title, message, detail, link, related_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, notif_type, title, message, detail, link, related_id))
        conn.commit()
        return cursor.lastrowid

    def create_task_notification(self, user_id, task_id, task_name, status, log_info=None, grader_id=None):
        """
        创建任务状态变更通知的便捷方法
        :param user_id: 接收通知的用户 ID
        :param task_id: 任务 ID
        :param task_name: 任务名称
        :param status: 任务状态 (pending, processing, success, failed)
        :param log_info: 日志信息
        :param grader_id: 批改核心 ID (用于生成链接)
        """
        # 状态对应的通知配置
        status_config = {
            'pending': {'type': 'task_pending', 'title': '任务排队中'},
            'processing': {'type': 'task_processing', 'title': '正在生成批改核心'},
            'success': {'type': 'task_success', 'title': '批改核心生成完成'},
            'failed': {'type': 'task_failed', 'title': '批改核心生成失败'}
        }

        config = status_config.get(status)
        if not config:
            return None

        # 构建链接
        link = f"/grader/{grader_id}" if grader_id else None

        # 截取 log_info
        detail = None
        if log_info:
            detail = log_info[:100] + '...' if len(log_info) > 100 else log_info

        return self.create_notification(
            user_id=user_id,
            notif_type=config['type'],
            title=config['title'],
            message=task_name,
            detail=detail,
            link=link,
            related_id=f"task_{task_id}"
        )

    def get_notifications(self, user_id, limit=20, include_read=False):
        """
        获取用户的通知列表
        :param user_id: 用户 ID
        :param limit: 返回数量限制
        :param include_read: 是否包含已读通知
        :return: 通知列表
        """
        conn = self.get_connection()
        sql = '''
            SELECT * FROM notifications
            WHERE user_id = ?
        '''
        params = [user_id]

        if not include_read:
            sql += " AND is_read = 0"

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def get_unread_notification_count(self, user_id):
        """获取用户未读通知数量"""
        conn = self.get_connection()
        row = conn.execute('''
            SELECT COUNT(*) as count FROM notifications
            WHERE user_id = ? AND is_read = 0
        ''', (user_id,)).fetchone()
        return row['count'] if row else 0

    def mark_notification_read(self, notification_id, user_id):
        """标记单条通知为已读"""
        conn = self.get_connection()
        conn.execute('''
            UPDATE notifications SET is_read = 1
            WHERE id = ? AND user_id = ?
        ''', (notification_id, user_id))
        conn.commit()

    def mark_all_notifications_read(self, user_id):
        """标记用户所有通知为已读"""
        conn = self.get_connection()
        conn.execute('''
            UPDATE notifications SET is_read = 1
            WHERE user_id = ? AND is_read = 0
        ''', (user_id,))
        conn.commit()

    def delete_notification(self, notification_id, user_id):
        """删除单条通知"""
        conn = self.get_connection()
        conn.execute('''
            DELETE FROM notifications
            WHERE id = ? AND user_id = ?
        ''', (notification_id, user_id))
        conn.commit()

    def delete_notifications_by_related_id(self, related_id):
        """根据关联 ID 删除通知（如任务删除时清理相关通知）"""
        conn = self.get_connection()
        conn.execute('''
            DELETE FROM notifications WHERE related_id = ?
        ''', (related_id,))
        conn.commit()

    def clean_old_notifications(self, days=30):
        """清理超过指定天数的已读通知"""
        conn = self.get_connection()
        conn.execute('''
            DELETE FROM notifications
            WHERE is_read = 1 AND created_at < datetime('now', ?)
        ''', (f'-{days} days',))
        conn.commit()

    def update_notification_by_related_id(self, related_id, notif_type=None, title=None, detail=None, link=None):
        """
        根据关联 ID 更新通知（用于任务状态变更时更新现有通知）
        """
        conn = self.get_connection()
        updates = []
        params = []

        if notif_type:
            updates.append("type = ?")
            params.append(notif_type)
        if title:
            updates.append("title = ?")
            params.append(title)
        if detail is not None:
            updates.append("detail = ?")
            params.append(detail)
        if link is not None:
            updates.append("link = ?")
            params.append(link)

        # 状态变更时重置为未读
        updates.append("is_read = 0")

        if updates:
            params.append(related_id)
            sql = f"UPDATE notifications SET {', '.join(updates)} WHERE related_id = ?"
            conn.execute(sql, params)
            conn.commit()

