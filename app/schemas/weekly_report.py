from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WeeklyReportCreate(BaseModel):
    enrollment_id: int
    week_no: int  # 0=分班测试，1..N=第N周
    level: str | None = None
    test_score: str | None = None
    attendance_pct: int | None = None
    teacher_comment: str | None = None
    parent_notified_at: datetime | None = None


class WeeklyReportOut(WeeklyReportCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
