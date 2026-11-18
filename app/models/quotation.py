from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Quotation(Base):
    """报价单（免费测试→出方案报价→比价→确认转报名）。"""

    __tablename__ = "quotations"
    __table_args__ = (UniqueConstraint("quote_no", name="uq_quote_no"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    quote_no: Mapped[str] = mapped_column(String(32))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    weeks: Mapped[int] = mapped_column(Integer)
    room_type: Mapped[str] = mapped_column(String(20))
    start_date: Mapped[date] = mapped_column(Date)  # 周日入学
    items: Mapped[list] = mapped_column(JSON)  # 明细快照 [{name, amount, currency, internal?}]
    total_usd: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(12), default="草稿")  # 草稿/已发送/已确认/已作废
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
