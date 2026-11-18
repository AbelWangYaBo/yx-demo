"""报价单：明细算价（纯函数）+ 流转（创建/确认转报名/作废）。

计价口径（research/04）：
- 学费按周计费，房型周价含食宿；注册费 USD 一次性且一律不退；
- 当地费（SSP/延签/水电/教材/押金）到校第一个周一以披索现付，不进 USD 总额；
- 学校返佣为内部核算项（对学员零服务费模式），仅后台展示。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import DEMO_ACTOR
from app.models import Course, Quotation, School
from app.services.audit import record_audit
from app.services.errors import ComplianceError, NotFound

LOCAL_FEE_PHP_PER_WEEK = Decimal("4850")  # SSP/延签/水电/教材等当地费预估


def _fmt(amount: Decimal) -> str:
    """3820.00 → '3820'；93.50 → '93.5'。"""
    text = str(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return text.rstrip("0").rstrip(".") if "." in text else text


def build_quote_items(registration_fee_usd, commission_rate, weekly_price, weeks: int,
                      room_type: str) -> tuple[list[dict], str]:
    """返回（明细项列表, USD 总额）。总额 = 学费 + 注册费。"""
    weekly = Decimal(str(weekly_price))
    tuition = weekly * weeks
    registration = Decimal(str(registration_fee_usd))
    local_php = LOCAL_FEE_PHP_PER_WEEK * weeks
    commission = tuition * Decimal(str(commission_rate)) / Decimal(100)
    items = [
        {
            "name": f"学费+食宿（USD {_fmt(weekly)}/周 × {weeks}周 · {room_type}）",
            "amount": _fmt(tuition), "currency": "USD",
        },
        {
            "name": "学校注册费（一次性，不退）",
            "amount": _fmt(registration), "currency": "USD",
        },
        {
            "name": "当地费预估（SSP/延签/水电/教材等，到校披索现付）",
            "amount": f"≈{int(local_php):,} PHP", "currency": "PHP",
        },
        {
            "name": f"学校返佣预估（{commission_rate}%，内部）",
            "amount": _fmt(commission), "currency": "USD", "internal": True,
        },
    ]
    total = tuition + registration
    return items, _fmt(total)


def _load_and_validate(session: Session, school_id: int, course_id: int,
                       weeks: int, room_type: str) -> tuple[School, Course]:
    school = session.get(School, school_id)
    course = session.get(Course, course_id)
    if school is None:
        raise NotFound("学校不存在")
    if course is None:
        raise NotFound("课程不存在")
    if course.school_id != school_id:
        raise ComplianceError(f"COURSE_SCHOOL_MISMATCH: 课程不属于该学校（{school.name}）")
    if weeks < course.min_weeks:
        raise ComplianceError(f"WEEKS_BELOW_MIN: 报名 {weeks} 周低于课程最短 {course.min_weeks} 周")
    if room_type not in (course.room_prices or {}):
        raise ComplianceError(
            f"ROOM_TYPE_INVALID: 房型「{room_type}」不在价目表内"
            f"（可选：{'/'.join((course.room_prices or {}).keys())}）"
        )
    return school, course


def preview_quote(session: Session, school_id: int, course_id: int, weeks: int,
                  room_type: str) -> dict:
    """实时算价（不落库）。"""
    school, course = _load_and_validate(session, school_id, course_id, weeks, room_type)
    items, total = build_quote_items(
        school.registration_fee_usd, school.commission_rate,
        course.room_prices[room_type], weeks, room_type,
    )
    return {
        "school_name": school.name, "course_name": course.name,
        "weeks": weeks, "room_type": room_type,
        "items": items, "total_usd": total,
    }


def next_quote_no(session: Session) -> str:
    year = date.today().year
    count = session.scalar(select(func.count()).select_from(Quotation)) or 0
    return f"QT-{year}-{count + 1:03d}"


def create_quotation(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Quotation:
    school, course = _load_and_validate(
        session, data.get("school_id"), data.get("course_id"),
        data.get("weeks") or 0, data.get("room_type") or "",
    )
    items, total = build_quote_items(
        school.registration_fee_usd, school.commission_rate,
        course.room_prices[data["room_type"]], data["weeks"], data["room_type"],
    )
    payload = {**data, "quote_no": next_quote_no(session), "items": items, "total_usd": total}
    if payload.get("status") not in ("草稿", "已发送"):
        payload["status"] = "草稿"
    from app.services import crud_helpers as ch

    quotation = ch._create(session, Quotation, payload, "quotation", actor)
    return quotation


def confirm_quotation(session: Session, quotation_id: int, actor: str = DEMO_ACTOR) -> Quotation:
    """确认报价 → 生成语言研修计划 + 报名（沿用报名全部合规校验）。"""
    quotation = session.get(Quotation, quotation_id)
    if quotation is None:
        raise NotFound("报价单不存在")
    if quotation.status in ("已确认", "已作废"):
        raise ComplianceError(
            f"QUOTE_ALREADY_CLOSED: 报价单状态为「{quotation.status}」，不可重复确认"
        )
    school = session.get(School, quotation.school_id)
    course = session.get(Course, quotation.course_id)
    return_date = quotation.start_date + timedelta(days=quotation.weeks * 7 - 1)

    from app.services import crud_helpers as ch

    program = ch.create_program(session, {
        "name": f"{school.name}·{course.name}（{quotation.weeks}周·{quotation.room_type}）",
        "type": "语言研修",
        "departure_date": quotation.start_date, "return_date": return_date,
        "school_id": quotation.school_id, "course_id": quotation.course_id,
        "weeks": quotation.weeks, "room_type": quotation.room_type,
        "status": "进行中",
    }, actor=actor)
    ch.create_enrollment(session, {
        "student_id": quotation.student_id, "program_id": program.id,
        "course_name": course.name, "accommodation": quotation.room_type,
        "pickup_arranged": True, "expected_start": quotation.start_date,
        "quotation_id": quotation.id,
    }, actor=actor)

    quotation.status = "已确认"
    quotation.confirmed_at = datetime.now()
    session.flush()
    record_audit(session, actor, "confirm", "quotation", quotation.quote_no,
                 {"status": "已确认", "enrollment_program": program.name})
    return quotation


def void_quotation(session: Session, quotation_id: int, actor: str = DEMO_ACTOR) -> Quotation:
    quotation = session.get(Quotation, quotation_id)
    if quotation is None:
        raise NotFound("报价单不存在")
    if quotation.status == "已确认":
        raise ComplianceError("QUOTE_CONFIRMED: 已确认报价已生成报名，不可作废（请走退费流程）")
    if quotation.status == "已作废":
        raise ComplianceError("QUOTE_ALREADY_VOID: 报价单已是作废状态")
    quotation.status = "已作废"
    session.flush()
    record_audit(session, actor, "void", "quotation", quotation.quote_no, {"status": "已作废"})
    return quotation
