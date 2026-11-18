from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SchoolCreate(BaseModel):
    name: str
    region: str  # 宿务/碧瑶/克拉克/马尼拉/怡朗
    country: str = "菲律宾"
    style: str  # 斯巴达/半斯巴达/自律型/度假村型
    commission_rate: str = "0"  # %
    registration_fee_usd: str = "0"
    cooperation_agreement: str | None = None
    verified: bool = False
    notes: str | None = None


class SchoolUpdate(BaseModel):
    name: str | None = None
    region: str | None = None
    country: str | None = None
    style: str | None = None
    commission_rate: str | None = None
    registration_fee_usd: str | None = None
    cooperation_agreement: str | None = None
    verified: bool | None = None
    notes: str | None = None


class SchoolOut(SchoolCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class CourseCreate(BaseModel):
    school_id: int
    name: str
    course_type: str  # ESL/密集ESL/IELTS保分/TOEIC保分/商务英语/亲子/冬夏令营/GAP
    lessons: str | None = None
    min_weeks: int = 4
    room_prices: dict  # {"4人间": 310, ...} USD/周
    guarantee: str | None = None
    notes: str | None = None


class CourseUpdate(BaseModel):
    school_id: int | None = None
    name: str | None = None
    course_type: str | None = None
    lessons: str | None = None
    min_weeks: int | None = None
    room_prices: dict | None = None
    guarantee: str | None = None
    notes: str | None = None


class CourseOut(CourseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
