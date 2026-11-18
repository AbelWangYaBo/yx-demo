from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Quotation
from app.schemas import QuotePreviewIn, QuotationCreate, QuotationOut
from app.services.quotation import (
    confirm_quotation,
    create_quotation,
    preview_quote,
    void_quotation,
)

router = APIRouter(prefix="/api/quotations", tags=["quotations"])


@router.get("", response_model=list[QuotationOut])
def list_quotations(student_id: int | None = None, session: Session = Depends(get_session)):
    stmt = select(Quotation).order_by(Quotation.id)
    if student_id:
        stmt = stmt.where(Quotation.student_id == student_id)
    return session.scalars(stmt).all()


@router.post("", response_model=QuotationOut, status_code=201)
def create_quotation_route(payload: QuotationCreate, session: Session = Depends(get_session)):
    return create_quotation(session, payload.model_dump())


@router.post("/preview")
def preview(payload: QuotePreviewIn, session: Session = Depends(get_session)):
    return preview_quote(session, **payload.model_dump())


@router.post("/{quotation_id}/confirm", response_model=QuotationOut)
def confirm(quotation_id: int, session: Session = Depends(get_session)):
    return confirm_quotation(session, quotation_id)


@router.post("/{quotation_id}/void", response_model=QuotationOut)
def void(quotation_id: int, session: Session = Depends(get_session)):
    return void_quotation(session, quotation_id)
