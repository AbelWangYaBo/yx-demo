from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Student(Base):
    """学员主索引：student_no 为机构内唯一业务标识。"""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    birth_date: Mapped[date] = mapped_column(Date)  # 未成年判定实时计算，不落冗余字段
    stage: Mapped[str] = mapped_column(String(20), default="意向")  # 生命周期：意向/沟通中/已报名/在读/已毕业/已流失
    guardian_name: Mapped[str | None] = mapped_column(String(100))
    guardian_phone: Mapped[str | None] = mapped_column(String(32))
    guardian_id_masked: Mapped[str | None] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
