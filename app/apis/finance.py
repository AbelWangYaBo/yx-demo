from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Payment, ServiceEvent
from app.schemas import PaymentCreate, PaymentOut, ServiceEventCreate, ServiceEventOut
from app.services import crud_helpers as ch
from app.services.errors import NotFound

payments_router = APIRouter(prefix="/api/payments", tags=["payments"])
events_router = APIRouter(prefix="/api/service-events", tags=["service-events"])


@payments_router.get("", response_model=list[PaymentOut])
def list_payments(session: Session = Depends(get_session)):
    return session.scalars(select(Payment)).all()


@payments_router.post("", response_model=PaymentOut, status_code=201)
def create_payment(payload: PaymentCreate, session: Session = Depends(get_session)):
    try:
        return ch.create_payment(session, payload.model_dump())
    except NotFound as e:
        raise HTTPException(404, str(e))


@events_router.get("", response_model=list[ServiceEventOut])
def list_service_events(session: Session = Depends(get_session)):
    return session.scalars(select(ServiceEvent)).all()


@events_router.post("", response_model=ServiceEventOut, status_code=201)
def create_service_event(payload: ServiceEventCreate, session: Session = Depends(get_session)):
    try:
        return ch.create_service_event(session, payload.model_dump())
    except NotFound as e:
        raise HTTPException(404, str(e))
