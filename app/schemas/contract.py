from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class ContractCreate(BaseModel):
    contract_no: str
    student_id: int
    service_scope: list[str] | None = None
    total_fee: str
    currency: str = "CNY"  # CNY/USD
    signed_date: date
    refund_rules: list[dict] | None = None
    status: str = "履行中"
    archived_date: date | None = None


class ContractOut(ContractCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RefundQuoteIn(BaseModel):
    stage: str


class RefundQuoteOut(BaseModel):
    contract_no: str
    stage: str
    total_fee: str
    refund_amount: str
