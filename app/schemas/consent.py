from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConsentCreate(BaseModel):
    student_id: int
    program_id: int | None = None
    consent_type: str  # 基础服务/敏感信息处理/信息出境/影像使用
    individual_consent: bool = False
    signer_name: str
    relation: str | None = None


class ConsentOut(ConsentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    signed_at: datetime
    status: str
    revoked_at: datetime | None = None
