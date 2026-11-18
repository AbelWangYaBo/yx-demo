from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class StudentCreate(BaseModel):
    student_no: str
    name: str
    birth_date: date
    stage: str = "意向"
    guardian_name: str | None = None
    guardian_phone: str | None = None
    guardian_id_masked: str | None = None
    notes: str | None = None


class StudentOut(StudentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
