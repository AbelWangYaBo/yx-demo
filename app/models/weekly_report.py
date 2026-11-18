from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WeeklyReport(Base):
    """在读周报（week_no=0 为入学分班测试；青少年营高频反馈、成人周报）。"""

    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.id"), index=True)
    week_no: Mapped[int] = mapped_column(Integer)  # 0=分班测试，1..N=第N周
    level: Mapped[str | None] = mapped_column(String(20))  # CEFR 或学校等级
    test_score: Mapped[str | None] = mapped_column(String(20))  # 周测/模考分数
    attendance_pct: Mapped[int | None] = mapped_column(Integer)  # 出勤率（保分班要求97-100%）
    teacher_comment: Mapped[str | None] = mapped_column(Text)
    parent_notified_at: Mapped[datetime | None] = mapped_column(DateTime)  # 家长反馈时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
