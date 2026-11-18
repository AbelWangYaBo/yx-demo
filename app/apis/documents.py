"""证件材料与沟通记录路由（出境游学：护照/签证/机票/学校材料/沟通记录）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import CommunicationLog, StudentDocument
from app.schemas import (
    CommunicationCreate,
    CommunicationOut,
    DocumentCreate,
    DocumentOut,
)
from app.services import crud_helpers as ch
from app.services.errors import NotFound

documents_router = APIRouter(prefix="/api/documents", tags=["documents"])
communications_router = APIRouter(prefix="/api/communications", tags=["communications"])


@documents_router.get("", response_model=list[DocumentOut])
def list_documents(student_id: int | None = None, session: Session = Depends(get_session)):
    stmt = select(StudentDocument)
    if student_id is not None:
        stmt = stmt.where(StudentDocument.student_id == student_id)
    return session.scalars(stmt).all()


@documents_router.post("", response_model=DocumentOut, status_code=201)
def create_document(payload: DocumentCreate, session: Session = Depends(get_session)):
    try:
        return ch.create_document(session, payload.model_dump())
    except NotFound as e:
        raise HTTPException(404, str(e))


@communications_router.get("", response_model=list[CommunicationOut])
def list_communications(student_id: int | None = None, session: Session = Depends(get_session)):
    stmt = select(CommunicationLog)
    if student_id is not None:
        stmt = stmt.where(CommunicationLog.student_id == student_id)
    return session.scalars(stmt).all()


@communications_router.post("", response_model=CommunicationOut, status_code=201)
def create_communication(payload: CommunicationCreate, session: Session = Depends(get_session)):
    try:
        return ch.create_communication(session, payload.model_dump())
    except NotFound as e:
        raise HTTPException(404, str(e))
