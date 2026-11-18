"""API 薄路由：仅做 schema 转换与调 services，无业务逻辑。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Staff
from app.schemas import AgencyCreate, AgencyOut, AgencyUpdate, StaffCreate, StaffOut, StaffUpdate
from app.services import crud_helpers as ch
from app.services.errors import NotFound

router = APIRouter(tags=["agency"])


@router.get("/api/agency", response_model=AgencyOut | None)
def get_agency(session: Session = Depends(get_session)):
    return ch.get_agency(session)


@router.post("/api/agency", response_model=AgencyOut, status_code=201)
def create_agency(payload: AgencyCreate, session: Session = Depends(get_session)):
    return ch.create_agency(session, payload.model_dump())


@router.patch("/api/agency", response_model=AgencyOut)
def update_agency(payload: AgencyUpdate, session: Session = Depends(get_session)):
    try:
        return ch.update_agency(session, payload.model_dump(exclude_unset=True))
    except NotFound as e:
        raise HTTPException(404, str(e))


staff_router = APIRouter(prefix="/api/staff", tags=["staff"])


@staff_router.get("", response_model=list[StaffOut])
def list_staff(session: Session = Depends(get_session)):
    from sqlalchemy import select

    return session.scalars(select(Staff)).all()


@staff_router.post("", response_model=StaffOut, status_code=201)
def create_staff(payload: StaffCreate, session: Session = Depends(get_session)):
    return ch.create_staff(session, payload.model_dump())


@staff_router.patch("/{staff_id}", response_model=StaffOut)
def update_staff(staff_id: int, payload: StaffUpdate, session: Session = Depends(get_session)):
    try:
        return ch.update_staff(session, staff_id, payload.model_dump(exclude_unset=True))
    except NotFound as e:
        raise HTTPException(404, str(e))
