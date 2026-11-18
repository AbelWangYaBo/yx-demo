from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Contract(Base):
    """服务合同（GF-2016-1002 骨架，保存≥30年）。"""

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_no: Mapped[str] = mapped_column(String(64), unique=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    service_scope: Mapped[list | None] = mapped_column(JSON)  # 服务范围勾选项
    total_fee: Mapped[str] = mapped_column(String(20))  # Decimal 字符串存储
    currency: Mapped[str] = mapped_column(String(8), default="CNY")  # CNY/USD
    signed_date: Mapped[date] = mapped_column(Date)
    archived_date: Mapped[date | None] = mapped_column(Date)
    refund_rules: Mapped[list | None] = mapped_column(JSON)  # 阶梯退费规则
    status: Mapped[str] = mapped_column(String(20), default="履行中")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
