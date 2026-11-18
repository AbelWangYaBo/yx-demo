from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Consent
from app.schemas import ConsentCreate, ConsentOut
from app.services import crud_helpers as ch
from app.services.errors import NotFound

router = APIRouter(prefix="/api/consents", tags=["consents"])


@router.get("", response_model=list[ConsentOut])
def list_consents(session: Session = Depends(get_session)):
    return session.scalars(select(Consent)).all()


@router.post("", response_model=ConsentOut, status_code=201)
def create_consent(payload: ConsentCreate, session: Session = Depends(get_session)):
    return ch.create_consent(session, payload.model_dump())


@router.post("/{consent_id}/revoke", response_model=ConsentOut)
def revoke_consent(consent_id: int, session: Session = Depends(get_session)):
    try:
        return ch.revoke_consent(session, consent_id)
    except NotFound as e:
        raise HTTPException(404, str(e))
