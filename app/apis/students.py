from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Student
from app.schemas import StudentCreate, StudentOut
from app.services import crud_helpers as ch
from app.services.aggregation import collect_student_records
from app.services.errors import StudentNotFound

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("", response_model=list[StudentOut])
def list_students(session: Session = Depends(get_session)):
    return session.scalars(select(Student)).all()


@router.post("", response_model=StudentOut, status_code=201)
def create_student(payload: StudentCreate, session: Session = Depends(get_session)):
    return ch.create_student(session, payload.model_dump())


@router.get("/paged")
def paged_students(keyword: str | None = None, page: int = 1, size: int = 20,
                   session: Session = Depends(get_session)):
    from app.services.student_directory import search_students

    return search_students(session, keyword=keyword, page=page, size=size)


@router.get("/{student_no}")
def get_student(student_no: str, session: Session = Depends(get_session)):
    from app.services.student_directory import view_student

    try:
        return view_student(session, student_no)
    except StudentNotFound as e:
        raise HTTPException(404, str(e))


@router.post("/{student_no}/stage", response_model=StudentOut)
def advance_student(student_no: str, payload: dict, session: Session = Depends(get_session)):
    from app.services.errors import ComplianceError
    from app.services.pipeline import advance_student_stage

    try:
        return advance_student_stage(session, student_no, payload.get("stage") or "",
                                     payload.get("remark"))
    except StudentNotFound as e:
        raise HTTPException(404, str(e))
    except ComplianceError as e:
        raise HTTPException(422, str(e))


@router.get("/{student_no}/records")
def student_records(student_no: str, session: Session = Depends(get_session)):
    from app.services.student_directory import view_student_records

    try:
        return view_student_records(session, student_no)
    except StudentNotFound as e:
        raise HTTPException(404, str(e))
