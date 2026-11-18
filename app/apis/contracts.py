from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Contract, Payment
from app.schemas import ContractCreate, ContractOut, RefundQuoteIn, RefundQuoteOut
from app.services import crud_helpers as ch
from app.services.finance import contract_settlement
from app.services.refund import calc_refund

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.get("")
def list_contracts(session: Session = Depends(get_session)):
    """合同列表（含财务对账扩展字段 settlement，故不走 response_model 过滤）。"""
    out = []
    for c in session.scalars(select(Contract)).all():
        payments = session.scalars(
            select(Payment).where(Payment.contract_id == c.id)
        ).all()
        out.append(
            ContractOut.model_validate(c).model_dump()
            | {"settlement": contract_settlement(c.total_fee, c.currency, payments)}
        )
    return out


@router.post("", response_model=ContractOut, status_code=201)
def create_contract(payload: ContractCreate, session: Session = Depends(get_session)):
    return ch.create_contract(session, payload.model_dump())


@router.post("/{contract_id}/refund-quote", response_model=RefundQuoteOut)
def refund_quote(contract_id: int, payload: RefundQuoteIn, session: Session = Depends(get_session)):
    contract = session.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(404, "合同不存在")
    try:
        amount = calc_refund(contract.total_fee, contract.refund_rules or [], payload.stage)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return RefundQuoteOut(
        contract_no=contract.contract_no, stage=payload.stage,
        total_fee=contract.total_fee, refund_amount=str(amount),
    )
