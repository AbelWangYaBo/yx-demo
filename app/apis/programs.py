from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Program
from app.schemas import ProgramCreate, ProgramOut, ProgramUpdate
from app.services import crud_helpers as ch
from app.services.errors import NotFound, ProgramViolation

router = APIRouter(prefix="/api/programs", tags=["programs"])


@router.get("", response_model=list[ProgramOut])
def list_programs(session: Session = Depends(get_session)):
    return session.scalars(select(Program)).all()


@router.post("", response_model=ProgramOut, status_code=201)
def create_program(payload: ProgramCreate, session: Session = Depends(get_session)):
    try:
        return ch.create_program(session, payload.model_dump())
    except ProgramViolation as e:
        raise HTTPException(422, {"violations": e.violations})


@router.patch("/{program_id}", response_model=ProgramOut)
def update_program(program_id: int, payload: ProgramUpdate, session: Session = Depends(get_session)):
    try:
        return ch.update_program(session, program_id, payload.model_dump(exclude_unset=True))
    except NotFound as e:
        raise HTTPException(404, str(e))
    except ProgramViolation as e:
        raise HTTPException(422, {"violations": e.violations})
