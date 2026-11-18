from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StudentDocument(Base):
    """学员证件与材料：护照/签证/机票/报名表/学校材料/健康证明/其他。"""

    __tablename__ = "student_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"))
    doc_type: Mapped[str] = mapped_column(String(40))  # 护照/签证/机票/报名表/学校材料/健康证明/其他
    doc_no: Mapped[str | None] = mapped_column(String(120))  # 证件号/航班号/学校名等
    issued_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    file_ref: Mapped[str | None] = mapped_column(Text)  # 材料说明（附件上传后以 attachment_id 关联）
    attachment_id: Mapped[int | None] = mapped_column(ForeignKey("attachments.id"))
    remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CommunicationLog(Base):
    """报名/服务沟通记录：电话/微信/邮件/面谈，双向留痕。"""

    __tablename__ = "communication_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"))
    channel: Mapped[str] = mapped_column(String(20))  # 电话/微信/邮件/面谈/其他
    direction: Mapped[str] = mapped_column(String(10))  # 呼出/呼入
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    operator: Mapped[str] = mapped_column(String(100))
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
