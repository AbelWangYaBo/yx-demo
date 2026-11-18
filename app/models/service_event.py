from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ServiceEvent(Base):
    """服务时间线节点（退费争议举证核心，逐节点留痕）。"""

    __tablename__ = "service_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id"))
    event_type: Mapped[str] = mapped_column(String(40))  # 材料递交/院校申请/offer接收/递签/签证结果/其他
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    operator: Mapped[str] = mapped_column(String(100))
    remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
