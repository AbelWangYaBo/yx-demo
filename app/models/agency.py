from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Agency(Base):
    """机构合规档案（841号令备案 + 旅行社资质）。"""

    __tablename__ = "agencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    uscc: Mapped[str] = mapped_column(String(32), unique=True)  # 统一社会信用代码
    travel_license_no: Mapped[str | None] = mapped_column(String(64))
    outbound_licensed: Mapped[bool] = mapped_column(Boolean, default=False)
    license_expiry: Mapped[date | None] = mapped_column(Date)
    filing_status: Mapped[str] = mapped_column(String(20), default="未备案")  # 841号令出入境中介备案
    filing_no: Mapped[str | None] = mapped_column(String(64))
    filing_date: Mapped[date | None] = mapped_column(Date)
    premise_proof: Mapped[str | None] = mapped_column(Text)  # 经营场所权属/租赁证明
    policy_documents: Mapped[list | None] = mapped_column(JSON)  # 制度文件清单（数据安全/资料保存等）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
