from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class ProgramCreate(BaseModel):
    name: str
    type: str  # 境内研学/出境游学/留学服务
    departure_date: date
    return_date: date
    filing_date: date | None = None
    filing_status: str = "未备案"
    dest_country_count: int | None = None
    max_cities_per_country: int | None = None
    student_age_group: str | None = None
    teacher_count: int = 0
    student_count: int | None = None
    insurance: dict | None = None
    emergency_plan: bool = False
    partner_school: str | None = None  # 境外合作学校/机构（出境游学必填）
    school_verified: bool | None = None
    status: str = "筹备中"
    # ---- 语言研修（个人计划）专有 ----
    school_id: int | None = None
    course_id: int | None = None
    weeks: int | None = None
    room_type: str | None = None


class ProgramUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    departure_date: date | None = None
    return_date: date | None = None
    filing_date: date | None = None
    filing_status: str | None = None
    dest_country_count: int | None = None
    max_cities_per_country: int | None = None
    student_age_group: str | None = None
    teacher_count: int | None = None
    student_count: int | None = None
    insurance: dict | None = None
    emergency_plan: bool | None = None
    partner_school: str | None = None
    school_verified: bool | None = None
    status: str | None = None
    school_id: int | None = None
    course_id: int | None = None
    weeks: int | None = None
    room_type: str | None = None


class ProgramOut(ProgramCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: object
