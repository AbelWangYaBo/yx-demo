from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    contract_id: int
    type: str  # 定金/服务费/代收代缴-学费/代收代缴-注册费/代收代缴-当地费
    amount: str
    currency: str = "CNY"  # CNY/USD/PHP
    voucher_no: str
    payee: str
    proof_file: str | None = None


class PaymentOut(PaymentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
