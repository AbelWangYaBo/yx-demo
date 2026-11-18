from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Enrollment(Base):
    """报名关系（备案材料：健康证明、家长告知书）。"""

    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "program_id", name="uq_student_program"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    stage: Mapped[str] = mapped_column(String(20), default="已报名")  # 已报名/材料准备/已缴费/已入学/在读/已毕业/已终止
    course_name: Mapped[str | None] = mapped_column(String(200))  # 课程
    accommodation: Mapped[str | None] = mapped_column(String(200))  # 住宿安排
    pickup_arranged: Mapped[bool] = mapped_column(Boolean, default=False)  # 接机
    expected_start: Mapped[date | None] = mapped_column(Date)  # 预计入学日期
    health_proof: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_notice_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    quotation_id: Mapped[int | None] = mapped_column(ForeignKey("quotations.id"))  # 报价单来源
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
