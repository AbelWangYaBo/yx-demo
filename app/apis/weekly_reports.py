from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import WeeklyReport
from app.schemas import WeeklyReportCreate, WeeklyReportOut
from app.services import crud_helpers as ch

router = APIRouter(prefix="/api/weekly-reports", tags=["weekly-reports"])


@router.get("", response_model=list[WeeklyReportOut])
def list_reports(enrollment_id: int | None = None, session: Session = Depends(get_session)):
    stmt = select(WeeklyReport).order_by(WeeklyReport.enrollment_id, WeeklyReport.week_no)
    if enrollment_id:
        stmt = stmt.where(WeeklyReport.enrollment_id == enrollment_id)
    return session.scalars(stmt).all()


@router.post("", response_model=WeeklyReportOut, status_code=201)
def create_report(payload: WeeklyReportCreate, session: Session = Depends(get_session)):
    return ch.create_weekly_report(session, payload.model_dump())
