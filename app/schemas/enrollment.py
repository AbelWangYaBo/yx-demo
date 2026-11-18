from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class EnrollmentCreate(BaseModel):
    student_id: int
    program_id: int | None = None  # 团体营报名必填；语言研修直建时可空
    course_name: str | None = None
    accommodation: str | None = None
    pickup_arranged: bool = False
    expected_start: date | None = None
    health_proof: bool = False
    parent_notice_signed: bool = False
    # ---- 语言研修直建（无现成项目时，事务内先建个人研修计划再报名）----
    school_id: int | None = None
    course_id: int | None = None
    weeks: int | None = None
    room_type: str | None = None
    start_date: date | None = None


class EnrollmentOut(EnrollmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    stage: str
    quotation_id: int | None = None
    created_at: datetime
