"""阶梯退费计算测试（GF-2016-1002 骨架）。"""
from decimal import Decimal

from app.services.refund import calc_refund

RULES = [
    {"stage": "未递交材料", "ratio": "100"},
    {"stage": "已递交未录取", "ratio": "70"},
    {"stage": "已获录取未递签", "ratio": "50"},
    {"stage": "已递签", "ratio": "20"},
    {"stage": "已出签", "ratio": "0"},
]


def test_full_refund_before_submission():
    assert calc_refund(Decimal("30000"), RULES, "未递交材料") == Decimal("30000.00")


def test_partial_refund_after_submission():
    assert calc_refund(Decimal("30000"), RULES, "已递交未录取") == Decimal("21000.00")


def test_zero_refund_after_visa_issued():
    assert calc_refund(Decimal("30000"), RULES, "已出签") == Decimal("0.00")


def test_unknown_stage_raises():
    import pytest

    with pytest.raises(ValueError):
        calc_refund(Decimal("30000"), RULES, "不存在的阶段")
