from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Staff(Base):
    """备案人员（841号令：机构统一办理人员备案）。"""

    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(primary_key=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("agencies.id"))
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(40))  # 法定代表人/管理人员/顾问
    id_card_masked: Mapped[str | None] = mapped_column(String(32))
    no_crime_declaration: Mapped[bool] = mapped_column(Boolean, default=False)
    filing_status: Mapped[str] = mapped_column(String(20), default="未备案")
    filing_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
