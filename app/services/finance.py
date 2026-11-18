"""财务对账：多币种折算（演示汇率）+ 合同应收/实收/差额。

口径（research/04 菲律宾资金链）：
- 应收 = 合同总额（学费+注册费口径，USD 或 CNY），折 CNY；
- 实收 = 定金/服务费/学费/注册费类缴费折 CNY 合计；
- 「代收代缴-当地费」（PHP，到校现付给学校）不计入实收对账，单独列示——
  否则虚增机构代收进度（该款项不经过机构账，学员到校直接付学校）。
- 汇率为 DEMO_FX_TO_CNY 静态演示值，非实时牌价。
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.config import DEMO_FX_TO_CNY

LOCAL_FEE_TYPE = "代收代缴-当地费"


def fx_to_cny(amount, currency: str, fx: dict | None = None) -> Decimal:
    """任意币种金额折算 CNY（演示汇率；未知币种抛 ValueError）。"""
    rates = {k: Decimal(v) for k, v in (fx or DEMO_FX_TO_CNY).items()}
    if currency not in rates:
        raise ValueError(f"未知币种: {currency}（可选 {'/'.join(rates)}）")
    value = Decimal(str(amount)) * rates[currency]
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def contract_settlement(total_fee, contract_currency: str, payments: list) -> dict:
    """合同对账：应收/实收/差额（均折 CNY）+ 当地费单列。

    payments 为该合同缴费记录（对象需有 type/amount/currency 属性）。
    """
    receivable = fx_to_cny(total_fee, contract_currency)
    paid = Decimal("0")
    local_fee_cny = Decimal("0")
    for p in payments:
        try:
            amount_cny = fx_to_cny(p.amount, p.currency)
        except (ValueError, InvalidOperation):
            continue
        if p.type == LOCAL_FEE_TYPE:
            local_fee_cny += amount_cny
        else:
            paid += amount_cny
    balance = (receivable - paid).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "receivable_cny": str(receivable),
        "paid_cny": str(paid.quantize(Decimal("0.01"))),
        "balance_cny": str(balance),
        "cleared": balance <= 0,
        "local_fee_cny": str(local_fee_cny.quantize(Decimal("0.01"))),
    }
