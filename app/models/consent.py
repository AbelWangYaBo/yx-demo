from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Consent(Base):
    """监护人同意管理（PIPL 第29/31条：单独同意、可撤回）。"""

    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"))
    consent_type: Mapped[str] = mapped_column(String(40))  # 基础服务/敏感信息处理/信息出境/影像使用
    individual_consent: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否单独同意
    signer_name: Mapped[str] = mapped_column(String(100))
    relation: Mapped[str | None] = mapped_column(String(40))
    signed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[str] = mapped_column(String(10), default="有效")  # 有效/撤回
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
