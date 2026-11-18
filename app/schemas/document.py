from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    student_id: int
    program_id: int | None = None
    doc_type: str  # 护照/签证/机票/报名表/学校材料/健康证明/其他
    doc_no: str | None = None
    issued_date: date | None = None
    expiry_date: date | None = None
    file_ref: str | None = None
    attachment_id: int | None = None
    remark: str | None = None


class DocumentOut(DocumentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class CommunicationCreate(BaseModel):
    student_id: int
    program_id: int | None = None
    channel: str  # 电话/微信/邮件/面谈/其他
    direction: str  # 呼出/呼入
    occurred_at: datetime
    operator: str
    summary: str


class CommunicationOut(CommunicationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
