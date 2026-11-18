from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.services.overview import overview
from app.services.retention import get_retention

router = APIRouter(tags=["compliance"])


@router.get("/api/compliance/overview")
def compliance_overview(session: Session = Depends(get_session)):
    return overview(session)


@router.get("/api/meta/retention")
def meta_retention():
    return get_retention()
