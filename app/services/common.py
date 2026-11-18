"""通用工具：未成年/周岁判定等。"""
from __future__ import annotations

from datetime import date


def age_years(birth_date: date, on_date: date | None = None) -> int:
    """周岁（默认按当天；WEG 等按出发日口径传入 on_date）。"""
    on_date = on_date or date.today()
    return on_date.year - birth_date.year - (
        (on_date.month, on_date.day) < (birth_date.month, birth_date.day)
    )


def is_minor(birth_date: date, today: date | None = None) -> bool:
    """按周岁判定是否未成年（PIPL 第31条口径：不满十四周岁另有专门规则，
    系统对全部未成年人统一要求监护人同意）。"""
    return age_years(birth_date, today) < 18
