# services/stats_service.py
"""
统计数据服务
负责聚合仪表盘所需的统计数据，包括班级数、学生数、批改核心数、待处理任务数等
支持会话级缓存以提高性能
"""

import os
from datetime import datetime, timedelta
from database import Database
from grading_core.factory import GraderFactory
from config import Config


class StatsService:
    """统计数据服务类"""

    # 缓存键前缀
    CACHE_KEY_STATS = 'dashboard_stats'
    CACHE_KEY_ACTIVITIES = 'recent_activities'
    CACHE_TTL_SECONDS = 300  # 5分钟缓存

    def __init__(self, session):
        """
        初始化统计服务
        :param session: Flask session 对象，用于缓存
        """
        self.session = session
        self.db = Database()

    def _get_cache(self, key):
        """从会话中获取缓存数据"""
        cache_entry = self.session.get(key)
        if cache_entry:
            timestamp = cache_entry.get('timestamp')
            if timestamp:
                cached_time = datetime.fromisoformat(timestamp)
                if datetime.now() - cached_time < timedelta(seconds=self.CACHE_TTL_SECONDS):
                    return cache_entry.get('data')
        return None

    def _set_cache(self, key, data):
        """将数据存入会话缓存"""
        self.session[key] = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

    def _clear_cache(self, key=None):
        """清除缓存"""
        if key:
            self.session.pop(key, None)
        else:
            self.session.pop(self.CACHE_KEY_STATS, None)
            self.session.pop(self.CACHE_KEY_ACTIVITIES, None)

    def get_dashboard_stats(self, user_id):
        """
        获取仪表盘统计数据
        :param user_id: 用户ID
        :return: dict {
            'class_count': int,
            'student_count': int,
            'grader_count': int,
            'pending_task_count': int
        }
        """
        # 尝试从缓存获取
        cached = self._get_cache(self.CACHE_KEY_STATS)
        if cached:
            return cached

        # 查询班级数量
        classes = self.db.get_classes(user_id)
        class_count = len(classes)

        # 查询学生总数（去重）
        conn = self.db.get_connection()
        student_count_row = conn.execute('''
            SELECT COUNT(DISTINCT s.student_id) as count
            FROM students s
            JOIN classes c ON s.class_id = c.id
            WHERE c.created_by = ?
        ''', (user_id,)).fetchone()
        student_count = student_count_row['count'] if student_count_row else 0

        # 查询批改核心数量
        grader_count = len(GraderFactory.get_all_strategies())

        # 查询待处理任务数
        pending_tasks_row = conn.execute('''
            SELECT COUNT(*) as count
            FROM ai_tasks
            WHERE created_by = ? AND status IN ('pending', 'processing')
        ''', (user_id,)).fetchone()
        pending_task_count = pending_tasks_row['count'] if pending_tasks_row else 0

        stats = {
            'class_count': class_count,
            'student_count': student_count,
            'grader_count': grader_count,
            'pending_task_count': pending_task_count
        }

        # 存入缓存
        self._set_cache(self.CACHE_KEY_STATS, stats)

        return stats

    def get_recent_activities(self, user_id, limit=5):
        """
        获取最近活动列表
        :param user_id: 用户ID
        :param limit: 返回数量限制
        :return: dict {
            'recent_classes': list,
            'recent_graders': list
        }
        """
        # 尝试从缓存获取
        cached = self._get_cache(self.CACHE_KEY_ACTIVITIES)
        if cached:
            return cached

        conn = self.db.get_connection()

        # 获取最近创建的班级（使用 id 作为时间代理，因为 classes 表没有 created_at）
        recent_classes_rows = conn.execute('''
            SELECT id, name, course
            FROM classes
            WHERE created_by = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()

        recent_classes = []
        for row in recent_classes_rows:
            # 使用 id 作为时间的粗略代理
            recent_classes.append({
                'id': row['id'],
                'name': row['name'],
                'course': row['course'],
                'created_at': None,
                'created_at_relative': '最近'
            })

        # 获取最近生成的批改核心（从 ai_tasks 表）
        recent_graders_rows = conn.execute('''
            SELECT id, name, grader_id, created_at
            FROM ai_tasks
            WHERE created_by = ? AND grader_id IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()

        recent_graders = []
        for row in recent_graders_rows:
            created_at = None
            if row['created_at']:
                try:
                    created_at = datetime.fromisoformat(row['created_at'])
                except:
                    created_at = datetime.now()
            else:
                created_at = datetime.now()

            recent_graders.append({
                'id': row['grader_id'],
                'task_id': row['id'],
                'name': row['name'],
                'created_at': row['created_at'],
                'created_at_relative': self._format_relative_time(created_at)
            })

        activities = {
            'recent_classes': recent_classes,
            'recent_graders': recent_graders
        }

        # 存入缓存
        self._set_cache(self.CACHE_KEY_ACTIVITIES, activities)

        return activities

    def _format_relative_time(self, dt):
        """
        格式化相对时间（如"2小时前"）
        :param dt: datetime 对象
        :return: str
        """
        now = datetime.now()
        diff = now - dt

        seconds = diff.total_seconds()

        if seconds < 60:
            return '刚刚'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes} 分钟前'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} 小时前'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days} 天前'
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f'{weeks} 周前'
        else:
            months = int(seconds / 2592000)
            return f'{months} 月前'

    def refresh_cache(self, user_id):
        """
        刷新缓存（手动触发）
        :param user_id: 用户ID
        :return: dict 包含最新的统计数据和活动
        """
        self._clear_cache()

        stats = self.get_dashboard_stats(user_id)
        activities = self.get_recent_activities(user_id)

        return {
            **stats,
            **activities
        }

    def get_all_data(self, user_id):
        """
        获取仪表盘所有数据（统计 + 活动）
        :param user_id: 用户ID
        :return: dict 合并的统计数据
        """
        stats = self.get_dashboard_stats(user_id)
        activities = self.get_recent_activities(user_id)

        return {
            **stats,
            **activities
        }
