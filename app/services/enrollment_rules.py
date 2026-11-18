"""报名附加校验：出境护照有效期（≥离校后6个月）+ WEG（未满15岁出境）。"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Program, Student, StudentDocument
from app.services.common import age_years

PASSPORT_VALIDITY_MONTHS = 6
OUTBOUND_TYPES = ("出境游学", "语言研修")
WEG_AGE_LIMIT = 15
WEG_PROOF_DOCS = ("WEG", "监护同行证明")


def passport_valid_until(session: Session, student_id: int) -> date | None:
    """学员当前护照的有效期至（取最新到期日）。"""
    doc = session.scalars(
        select(StudentDocument)
        .where(StudentDocument.student_id == student_id, StudentDocument.doc_type == "护照")
        .order_by(StudentDocument.expiry_date.desc())
    ).first()
    return doc.expiry_date if doc else None


def required_valid_until(return_date: date) -> date:
    """护照须有效至行程结束后6个日历月（边检惯例：有效期不足6个月不予出境）。"""
    total = return_date.month - 1 + PASSPORT_VALIDITY_MONTHS
    year, month_index = divmod(total, 12)
    month = month_index + 1
    try:
        return date(return_date.year + year, month, return_date.day)
    except ValueError:  # 目标月无此日（如31日），取月末
        if month == 12:
            return date(return_date.year + year + 1, 1, 1) - timedelta(days=1)
        return date(return_date.year + year, month + 1, 1) - timedelta(days=1)


def check_passport(session: Session, student_id: int, program: Program) -> str | None:
    """返回错误消息；None 表示通过。出境游学与语言研修（均为出境）需要。"""
    if program.type not in OUTBOUND_TYPES:
        return None
    need = required_valid_until(program.return_date)
    expiry = passport_valid_until(session, student_id)
    if expiry is None:
        return (
            f"PASSPORT_REQUIRED: 出境项目须先登记学员护照信息"
            f"（须有效至行程结束后6个月，即 {need.isoformat()} 之后）"
        )
    if expiry < need:
        return (
            f"PASSPORT_INVALID: 护照有效期至 {expiry.isoformat()}，不足行程结束后6个月"
            f"（须有效至 {need.isoformat()} 之后），不予报名"
        )
    return None


def check_weg(session: Session, student: Student, program: Program) -> str | None:
    """未满15周岁（按出发日）报名出境项目，须已登记 WEG 或监护同行证明。

    菲律宾口径：15 岁以下不可单独入境，父母不同行须办 WEG 公证；
    亲子课程家长同行的，登记监护同行证明即可。
    """
    if program.type not in OUTBOUND_TYPES:
        return None
    if age_years(student.birth_date, program.departure_date) >= WEG_AGE_LIMIT:
        return None
    proof = session.scalars(
        select(StudentDocument.id)
        .where(
            StudentDocument.student_id == student.id,
            StudentDocument.doc_type.in_(WEG_PROOF_DOCS),
        )
        .limit(1)
    ).first()
    if proof is None:
        return (
            "WEG_REQUIRED: 学员出发日未满 15 周岁，须先在证件材料中登记 "
            "WEG（父母不同行，公证办理）或监护同行证明（家长同校/同行）后方可报名"
        )
    return None
