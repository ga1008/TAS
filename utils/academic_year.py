"""学年学期推断工具函数"""
from datetime import datetime


def infer_academic_year_semester(date=None):
    """根据日期推断学年学期

    规则:
    - 9月-12月: 当年-次年学年度第一学期
    - 1月: 上年-当年学年度第一学期（期末考试期间）
    - 2月-8月: 上年-当年学年度第二学期

    Args:
        date: 日期对象，默认为当前日期

    Returns:
        str: 学年学期字符串，如 "2025-2026学年度第一学期"
    """
    if date is None:
        date = datetime.now()

    year = date.year
    month = date.month

    if 9 <= month <= 12:
        # 9月-12月：当前学年第一学期
        return f"{year}-{year+1}学年度第一学期"
    elif month == 1:
        # 1月：上一学年第一学期（期末考试期间）
        return f"{year-1}-{year}学年度第一学期"
    else:
        # 2月-8月：上一学年第二学期
        return f"{year-1}-{year}学年度第二学期"
