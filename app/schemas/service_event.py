from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceEventCreate(BaseModel):
    student_id: int
    contract_id: int | None = None
    event_type: str
    occurred_at: datetime
    operator: str
    remark: str | None = None


class ServiceEventOut(ServiceEventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
