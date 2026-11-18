from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Program(Base):
    """可报名项目：团体营（境内研学/出境游学，备案制）或个人语言研修计划。"""

    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20))  # 境内研学/出境游学/语言研修/留学服务
    departure_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date] = mapped_column(Date)
    filing_date: Mapped[date | None] = mapped_column(Date)
    filing_status: Mapped[str] = mapped_column(String(20), default="未备案")
    dest_country_count: Mapped[int | None] = mapped_column()
    max_cities_per_country: Mapped[int | None] = mapped_column()
    student_age_group: Mapped[str | None] = mapped_column(String(20))  # 小学/中学/混合
    teacher_count: Mapped[int] = mapped_column(default=0)
    student_count: Mapped[int | None] = mapped_column()
    insurance: Mapped[dict | None] = mapped_column(JSON)
    emergency_plan: Mapped[bool] = mapped_column(Boolean, default=False)
    partner_school: Mapped[str | None] = mapped_column(String(200))  # 境外合作学校/机构（出境游学必填）
    school_verified: Mapped[bool | None] = mapped_column()  # 境外学校资质已核验（对照涉外监管网）
    status: Mapped[str] = mapped_column(String(20), default="筹备中")  # 筹备中/已成团/进行中/结束
    # ---- 语言研修（个人计划）专有 ----
    school_id: Mapped[int | None] = mapped_column(ForeignKey("schools.id"))
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"))
    weeks: Mapped[int | None] = mapped_column(Integer)
    room_type: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
