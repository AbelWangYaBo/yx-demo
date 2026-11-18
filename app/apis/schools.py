from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Course, School
from app.schemas import CourseCreate, CourseOut, CourseUpdate, SchoolCreate, SchoolOut, SchoolUpdate
from app.services import crud_helpers as ch

router = APIRouter(prefix="/api/schools", tags=["schools"])
courses_router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=list[SchoolOut])
def list_schools(session: Session = Depends(get_session)):
    return session.scalars(select(School).order_by(School.id)).all()


@router.post("", response_model=SchoolOut, status_code=201)
def create_school(payload: SchoolCreate, session: Session = Depends(get_session)):
    return ch.create_school(session, payload.model_dump())


@router.patch("/{school_id}", response_model=SchoolOut)
def update_school(school_id: int, payload: SchoolUpdate, session: Session = Depends(get_session)):
    return ch.update_school(session, school_id, payload.model_dump(exclude_unset=True))


@courses_router.get("", response_model=list[CourseOut])
def list_courses(session: Session = Depends(get_session)):
    return session.scalars(select(Course).order_by(Course.id)).all()


@courses_router.post("", response_model=CourseOut, status_code=201)
def create_course(payload: CourseCreate, session: Session = Depends(get_session)):
    return ch.create_course(session, payload.model_dump())


@courses_router.patch("/{course_id}", response_model=CourseOut)
def update_course(course_id: int, payload: CourseUpdate, session: Session = Depends(get_session)):
    return ch.update_course(session, course_id, payload.model_dump(exclude_unset=True))
