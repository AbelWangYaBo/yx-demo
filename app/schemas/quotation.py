from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class QuotationCreate(BaseModel):
    student_id: int
    school_id: int
    course_id: int
    weeks: int
    room_type: str
    start_date: date
    status: str = "草稿"  # 草稿/已发送


class QuotationOut(QuotationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    quote_no: str
    items: list
    total_usd: str
    created_at: datetime
    confirmed_at: datetime | None = None


class QuotePreviewIn(BaseModel):
    """报价预览（不落库）：学校+课程+周数+房型 → 明细。"""

    school_id: int
    course_id: int
    weeks: int
    room_type: str
