from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Payment(Base):
    """缴费凭证链（区分服务费/代收代缴，代收代缴须关联收费方证明）。"""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), index=True)
    type: Mapped[str] = mapped_column(String(24))  # 定金/服务费/代收代缴-学费/代收代缴-注册费/代收代缴-当地费
    amount: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(8), default="CNY")  # CNY/USD/PHP
    voucher_no: Mapped[str] = mapped_column(String(64))
    payee: Mapped[str] = mapped_column(String(200))
    proof_file: Mapped[str | None] = mapped_column(Text)  # 代收代缴：收费方合法证明文件
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
