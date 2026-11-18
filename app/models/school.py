from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class School(Base):
    """合作学校库（841号令「与境外服务机构合作协议」备案要件的载体）。"""

    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    region: Mapped[str] = mapped_column(String(20))  # 宿务/碧瑶/克拉克/马尼拉/怡朗
    country: Mapped[str] = mapped_column(String(40), default="菲律宾")
    style: Mapped[str] = mapped_column(String(20))  # 斯巴达/半斯巴达/自律型/度假村型
    commission_rate: Mapped[str] = mapped_column(String(8), default="0")  # 学校返佣（%）
    registration_fee_usd: Mapped[str] = mapped_column(String(12), default="0")  # 注册费（一次性，USD）
    cooperation_agreement: Mapped[str | None] = mapped_column(Text)  # 合作协议文件说明
    verified: Mapped[bool] = mapped_column(Boolean, default=False)  # 资质已核验
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Course(Base):
    """课程价目（按周计费，房型差价；挂学校）。"""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    course_type: Mapped[str] = mapped_column(String(20))  # ESL/密集ESL/IELTS保分/TOEIC保分/商务英语/亲子/冬夏令营/GAP
    lessons: Mapped[str | None] = mapped_column(String(100))  # 课时结构，如 1对1×4 + 团体×3
    min_weeks: Mapped[int] = mapped_column(Integer, default=4)
    room_prices: Mapped[dict] = mapped_column(JSON)  # {"4人间": 310, ...} USD/周（含食宿）
    guarantee: Mapped[str | None] = mapped_column(Text)  # 保分条款
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
