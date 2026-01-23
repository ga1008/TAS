"""
AI Conversation Service

Core service layer for AI assistant conversations, messages, and rate limiting.
All user stories depend on this service.

Feature: 002-global-ai-assistant
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


@dataclass
class Conversation:
    """对话会话数据类"""
    id: int
    user_id: int
    title: str = '新对话'
    status: str = 'active'  # active, archived
    created_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    message_count: int = 0

    @classmethod
    def from_row(cls, row: dict) -> 'Conversation':
        """从数据库行构建 Conversation 对象"""
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            title=row.get('title', '新对话'),
            status=row.get('status', 'active'),
            created_at=row.get('created_at'),
            last_active_at=row.get('last_active_at'),
            message_count=row.get('message_count', 0)
        )

    def to_dict(self) -> dict:
        """转换为字典用于 JSON 序列化"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'status': self.status,
            'created_at': str(self.created_at) if self.created_at else None,
            'last_active_at': str(self.last_active_at) if self.last_active_at else None,
            'message_count': self.message_count
        }


@dataclass
class Message:
    """对话消息数据类"""
    id: int
    conversation_id: int
    role: str  # user, assistant, system
    content: str
    trigger_type: str = 'user_message'  # user_message, page_change, operation_complete, system
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: dict) -> 'Message':
        """从数据库行构建 Message 对象"""
        metadata = None
        if row.get('metadata_json'):
            try:
                metadata = json.loads(row['metadata_json'])
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        return cls(
            id=row['id'],
            conversation_id=row['conversation_id'],
            role=row['role'],
            content=row['content'],
            trigger_type=row.get('trigger_type', 'user_message'),
            metadata=metadata or {},
            created_at=row.get('created_at')
        )

    def to_dict(self) -> dict:
        """转换为字典用于 JSON 序列化"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'trigger_type': self.trigger_type,
            'metadata': self.metadata,
            'created_at': str(self.created_at) if self.created_at else None
        }


@dataclass
class RateLimitRecord:
    """速率限制记录数据类"""
    user_id: int
    last_proactive_trigger: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: dict) -> 'RateLimitRecord':
        """从数据库行构建 RateLimitRecord 对象"""
        return cls(
            user_id=row['user_id'],
            last_proactive_trigger=row.get('last_proactive_trigger'),
            updated_at=row.get('updated_at')
        )


class AIConversationService:
    """
    AI 对话服务

    提供对话会话、消息、速率限制的 CRUD 操作。
    """

    def __init__(self, db):
        """
        初始化服务

        :param db: Database 实例
        """
        self.db = db

    # ==================== 对话管理 ====================

    def create_conversation(self, user_id: int, title: str = '新对话') -> Conversation:
        """
        创建新对话会话（会自动归档当前用户的其他活跃对话）

        :param user_id: 用户 ID
        :param title: 对话标题
        :return: 新创建的 Conversation 对象
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # 先归档用户现有的活跃对话
        cursor.execute('''
            UPDATE ai_conversations
            SET status = 'archived'
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))

        # 创建新对话
        cursor.execute('''
            INSERT INTO ai_conversations (user_id, title, status, created_at, last_active_at)
            VALUES (?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (user_id, title))
        conn.commit()

        conversation_id = cursor.lastrowid
        row = conn.execute(
            'SELECT * FROM ai_conversations WHERE id = ?',
            (conversation_id,)
        ).fetchone()

        return Conversation.from_row(dict(row))

    def get_active_conversation(self, user_id: int) -> Optional[Conversation]:
        """
        获取用户的活跃对话，如果没有则自动创建一个

        :param user_id: 用户 ID
        :return: Conversation 对象
        """
        conn = self.db.get_connection()

        # 查找活跃对话
        row = conn.execute('''
            SELECT c.*,
                   (SELECT COUNT(*) FROM ai_messages WHERE conversation_id = c.id) as message_count
            FROM ai_conversations c
            WHERE c.user_id = ? AND c.status = 'active'
            ORDER BY c.last_active_at DESC
            LIMIT 1
        ''', (user_id,)).fetchone()

        if row:
            return Conversation.from_row(dict(row))

        # 没有活跃对话，创建新的
        return self.create_conversation(user_id)

    def get_conversation_by_id(self, conversation_id: int, user_id: int) -> Optional[Conversation]:
        """
        根据 ID 获取对话（需验证用户权限）

        :param conversation_id: 对话 ID
        :param user_id: 用户 ID（用于权限验证）
        :return: Conversation 对象或 None
        """
        conn = self.db.get_connection()
        row = conn.execute('''
            SELECT c.*,
                   (SELECT COUNT(*) FROM ai_messages WHERE conversation_id = c.id) as message_count
            FROM ai_conversations c
            WHERE c.id = ? AND c.user_id = ?
        ''', (conversation_id, user_id)).fetchone()

        if row:
            return Conversation.from_row(dict(row))
        return None

    def archive_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        归档对话

        :param conversation_id: 对话 ID
        :param user_id: 用户 ID
        :return: 是否成功
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE ai_conversations
            SET status = 'archived'
            WHERE id = ? AND user_id = ?
        ''', (conversation_id, user_id))
        conn.commit()
        return cursor.rowcount > 0

    def update_conversation_activity(self, conversation_id: int):
        """
        更新对话的最后活跃时间

        :param conversation_id: 对话 ID
        """
        conn = self.db.get_connection()
        conn.execute('''
            UPDATE ai_conversations
            SET last_active_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (conversation_id,))
        conn.commit()

    # ==================== 消息管理 ====================

    def add_message(self, conversation_id: int, role: str, content: str,
                    trigger_type: str = 'user_message',
                    metadata: Optional[Dict[str, Any]] = None) -> Message:
        """
        添加消息到对话

        :param conversation_id: 对话 ID
        :param role: 角色 (user, assistant, system)
        :param content: 消息内容
        :param trigger_type: 触发类型
        :param metadata: 元数据
        :return: 新创建的 Message 对象
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None

        cursor.execute('''
            INSERT INTO ai_messages (conversation_id, role, content, trigger_type, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (conversation_id, role, content, trigger_type, metadata_json))
        conn.commit()

        message_id = cursor.lastrowid
        row = conn.execute(
            'SELECT * FROM ai_messages WHERE id = ?',
            (message_id,)
        ).fetchone()

        # 更新对话活跃时间
        self.update_conversation_activity(conversation_id)

        return Message.from_row(dict(row))

    def get_messages(self, conversation_id: int, limit: int = 20,
                     offset: int = 0, order: str = 'desc') -> tuple[List[Message], int]:
        """
        获取对话消息（支持分页）

        :param conversation_id: 对话 ID
        :param limit: 每页数量 (1-100)
        :param offset: 偏移量
        :param order: 排序 ('asc' 或 'desc')
        :return: (消息列表, 总数)
        """
        conn = self.db.get_connection()

        # 限制参数范围
        limit = max(1, min(100, limit))
        offset = max(0, offset)
        order_clause = 'DESC' if order.lower() == 'desc' else 'ASC'

        # 获取总数
        total_row = conn.execute(
            'SELECT COUNT(*) as total FROM ai_messages WHERE conversation_id = ?',
            (conversation_id,)
        ).fetchone()
        total = total_row['total'] if total_row else 0

        # 获取消息
        rows = conn.execute(f'''
            SELECT * FROM ai_messages
            WHERE conversation_id = ?
            ORDER BY created_at {order_clause}
            LIMIT ? OFFSET ?
        ''', (conversation_id, limit, offset)).fetchall()

        messages = [Message.from_row(dict(row)) for row in rows]

        return messages, total

    def get_recent_messages(self, conversation_id: int, limit: int = 10) -> List[Message]:
        """
        获取最近的消息（用于构建 AI 上下文）

        :param conversation_id: 对话 ID
        :param limit: 消息数量
        :return: 消息列表（按时间升序）
        """
        conn = self.db.get_connection()
        rows = conn.execute('''
            SELECT * FROM (
                SELECT * FROM ai_messages
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ) ORDER BY created_at ASC
        ''', (conversation_id, limit)).fetchall()

        return [Message.from_row(dict(row)) for row in rows]

    def get_messages_after(self, conversation_id: int, last_message_id: int) -> List[Message]:
        """
        获取指定消息之后的新消息（用于轮询同步）

        :param conversation_id: 对话 ID
        :param last_message_id: 已知的最后消息 ID
        :return: 新消息列表
        """
        conn = self.db.get_connection()
        rows = conn.execute('''
            SELECT * FROM ai_messages
            WHERE conversation_id = ? AND id > ?
            ORDER BY created_at ASC
        ''', (conversation_id, last_message_id)).fetchall()

        return [Message.from_row(dict(row)) for row in rows]

    def enforce_message_limit(self, conversation_id: int, max_messages: int = 100) -> int:
        """
        强制执行消息数量限制，删除最旧的消息

        :param conversation_id: 对话 ID
        :param max_messages: 最大消息数
        :return: 删除的消息数
        """
        conn = self.db.get_connection()

        # 获取当前消息数
        count_row = conn.execute(
            'SELECT COUNT(*) as cnt FROM ai_messages WHERE conversation_id = ?',
            (conversation_id,)
        ).fetchone()
        current_count = count_row['cnt'] if count_row else 0

        if current_count <= max_messages:
            return 0

        # 计算需要删除的数量
        delete_count = current_count - max_messages

        # 删除最旧的消息
        conn.execute('''
            DELETE FROM ai_messages
            WHERE id IN (
                SELECT id FROM ai_messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            )
        ''', (conversation_id, delete_count))
        conn.commit()

        return delete_count

    # ==================== 速率限制 ====================

    def check_rate_limit(self, user_id: int, cooldown_seconds: int = 60) -> tuple[bool, int]:
        """
        检查用户是否受速率限制

        :param user_id: 用户 ID
        :param cooldown_seconds: 冷却时间（秒）
        :return: (是否允许, 剩余冷却秒数)
        """
        conn = self.db.get_connection()
        row = conn.execute(
            'SELECT * FROM ai_rate_limits WHERE user_id = ?',
            (user_id,)
        ).fetchone()

        if not row:
            return True, 0

        last_trigger = row['last_proactive_trigger']
        if not last_trigger:
            return True, 0

        # 解析时间戳
        if isinstance(last_trigger, str):
            try:
                last_trigger = datetime.fromisoformat(last_trigger.replace('Z', '+00:00'))
            except ValueError:
                # 尝试其他格式
                try:
                    last_trigger = datetime.strptime(last_trigger, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return True, 0

        # 计算剩余冷却时间
        now = datetime.now()
        if last_trigger.tzinfo:
            now = datetime.now(last_trigger.tzinfo)

        elapsed = (now - last_trigger).total_seconds()
        remaining = cooldown_seconds - elapsed

        if remaining <= 0:
            return True, 0

        return False, int(remaining)

    def update_rate_limit(self, user_id: int):
        """
        更新用户的速率限制记录

        :param user_id: 用户 ID
        """
        conn = self.db.get_connection()

        # 使用 UPSERT 语法
        conn.execute('''
            INSERT INTO ai_rate_limits (user_id, last_proactive_trigger, updated_at)
            VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                last_proactive_trigger = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id,))
        conn.commit()

    def get_rate_limit_record(self, user_id: int) -> Optional[RateLimitRecord]:
        """
        获取用户的速率限制记录

        :param user_id: 用户 ID
        :return: RateLimitRecord 对象或 None
        """
        conn = self.db.get_connection()
        row = conn.execute(
            'SELECT * FROM ai_rate_limits WHERE user_id = ?',
            (user_id,)
        ).fetchone()

        if row:
            return RateLimitRecord.from_row(dict(row))
        return None
