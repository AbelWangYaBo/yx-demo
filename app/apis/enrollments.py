from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import EnrollmentCreate, EnrollmentOut
from app.services import crud_helpers as ch
from app.services.errors import ConsentRequired, NotFound

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])


@router.post("/{enrollment_id}/stage", response_model=EnrollmentOut)
def advance_enrollment(enrollment_id: int, payload: dict, session: Session = Depends(get_session)):
    from app.services.errors import ComplianceError
    from app.services.pipeline import advance_enrollment_stage

    try:
        return advance_enrollment_stage(session, enrollment_id, payload.get("stage") or "",
                                        payload.get("remark"))
    except ComplianceError as e:
        raise HTTPException(422, str(e))
    except NotFound as e:
        raise HTTPException(404, str(e))


@router.post("", response_model=EnrollmentOut, status_code=201)
def create_enrollment(payload: EnrollmentCreate, session: Session = Depends(get_session)):
    try:
        return ch.create_enrollment(session, payload.model_dump())
    except ConsentRequired as e:
        raise HTTPException(422, str(e))
    except NotFound as e:
        raise HTTPException(404, str(e))
