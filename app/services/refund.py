"""阶梯退费计算（GF-2016-1002 骨架：服务阶段 → 退费比例）。"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def calc_refund(total_fee, rules: list[dict], stage: str) -> Decimal:
    """按规则表计算指定阶段应退金额。

    - total_fee: int/str/Decimal 均可
    - rules: [{"stage": str, "ratio": str|number}]，ratio 为百分比数值
    - stage 不在规则表内 → ValueError
    """
    rule = next((r for r in rules if r["stage"] == stage), None)
    if rule is None:
        raise ValueError(f"未知服务阶段: {stage}")
    amount = Decimal(str(total_fee)) * Decimal(str(rule["ratio"])) / Decimal("100")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
