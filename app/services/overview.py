"""合规总览：备案状态、有效期预警、活动风险、审计链健康度 + 业务看板。

业务看板（领导/顾问/财务视角）：
- 转化漏斗：学员阶段分布 + 报价状态分布；
- 佣金拆分：已确认报价预估 vs 学员已入学的应结（学校按到校结算）；
- 材料到期预警：学员护照/签证/SSP/ACR 等到期日（已过期 error / 30天内 warning）；
- 顾问待办：报价超3天未确认、材料收集中、7天内入学。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    CommunicationLog,
    Contract,
    Enrollment,
    Program,
    Quotation,
    Staff,
    Student,
    StudentDocument,
)
from app.services import compliance as cpl
from app.services.audit import verify_chain
from app.services.crud_helpers import get_agency, program_check_data

DOC_EXPIRY_WARN_DAYS = 30
QUOTE_FOLLOW_DAYS = 3
ARRIVAL_SOON_DAYS = 7


def _business_stats(session: Session) -> dict:
    """业务看板：在读 / 待跟进报价 / 本月入学 / 佣金拆分（USD）。"""
    in_study = session.scalar(
        select(func.count()).select_from(Enrollment).where(Enrollment.stage == "在读")
    ) or 0
    pending_quotes = session.scalar(
        select(func.count()).select_from(Quotation).where(Quotation.status.in_(["草稿", "已发送"]))
    ) or 0
    today = date.today()
    month_start = today.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    arrivals = session.scalar(
        select(func.count()).select_from(Enrollment).where(
            Enrollment.expected_start >= month_start,
            Enrollment.expected_start < next_month,
            Enrollment.stage.in_(["已入学", "在读", "已毕业"]),
        )
    ) or 0
    est = Decimal("0")
    settleable = Decimal("0")
    for q in session.scalars(select(Quotation).where(Quotation.status == "已确认")).all():
        item = next((i for i in (q.items or []) if i.get("internal")), None)
        if not item:
            continue
        try:
            amount = Decimal(str(item["amount"]).replace(",", ""))
        except InvalidOperation:
            continue
        est += amount
        # 学校按学员到校后与代理结算：报名推进到「已入学/在读/已毕业」才算应结
        stage = session.scalar(
            select(Enrollment.stage).where(Enrollment.quotation_id == q.id).limit(1)
        )
        if stage in ("已入学", "在读", "已毕业"):
            settleable += amount
    return {
        "in_study": in_study,
        "pending_quotes": pending_quotes,
        "arrivals_this_month": arrivals,
        "est_commission_usd": str(est),
        "settleable_commission_usd": str(settleable),
    }


def _funnel(session: Session) -> dict:
    """转化漏斗：学员生命周期分布 + 报价状态分布。"""
    student_stages = {
        row[0]: row[1]
        for row in session.execute(
            select(Student.stage, func.count()).group_by(Student.stage)
        ).all()
    }
    quote_status = {
        row[0]: row[1]
        for row in session.execute(
            select(Quotation.status, func.count()).group_by(Quotation.status)
        ).all()
    }
    return {"student_stages": student_stages, "quote_status": quote_status}


def _expiring_documents(session: Session) -> list[dict]:
    """学员材料到期预警：已过期 error / 30天内 warning（护照/签证/SSP/ACR 等）。"""
    today = date.today()
    out = []
    stmt = (
        select(StudentDocument, Student)
        .join(Student, StudentDocument.student_id == Student.id)
        .where(StudentDocument.expiry_date.is_not(None))
    )
    for doc, student in session.execute(stmt).all():
        days = (doc.expiry_date - today).days
        if days < 0:
            level, hint = "error", f"已过期 {-days} 天"
        elif days <= DOC_EXPIRY_WARN_DAYS:
            level, hint = "warning", f"{days} 天后到期"
        else:
            continue
        out.append(
            {
                "student_no": student.student_no,
                "student_name": student.name,
                "doc_type": doc.doc_type,
                "doc_no": doc.doc_no,
                "expiry_date": doc.expiry_date.isoformat(),
                "days_left": days,
                "level": level,
                "hint": hint,
            }
        )
    out.sort(key=lambda x: x["days_left"])
    return out


def _follow_ups(session: Session) -> list[dict]:
    """顾问待办：报价超3天未确认 / 材料收集中 / 7天内入学。"""
    today = date.today()
    out = []
    quote_deadline = datetime.now() - timedelta(days=QUOTE_FOLLOW_DAYS)
    for q, s in session.execute(
        select(Quotation, Student)
        .join(Student, Quotation.student_id == Student.id)
        .where(Quotation.status.in_(["草稿", "已发送"]))
    ).all():
        stale = (q.created_at or datetime.now()) < quote_deadline
        out.append(
            {
                "kind": "报价跟进" if stale else "待报价跟进",
                "student_no": s.student_no,
                "student_name": s.name,
                "detail": f"{q.quote_no}（{q.weeks}周·{q.room_type}，${q.total_usd}）状态 {q.status}",
                "urgent": stale,
            }
        )
    for e, s, p in session.execute(
        select(Enrollment, Student, Program)
        .join(Student, Enrollment.student_id == Student.id)
        .join(Program, Enrollment.program_id == Program.id)
        .where(Enrollment.stage.in_(["已报名", "材料准备", "已缴费"]))
    ).all():
        if e.stage == "材料准备":
            out.append(
                {
                    "kind": "材料收集中",
                    "student_no": s.student_no,
                    "student_name": s.name,
                    "detail": f"{p.name}｜待收材料/证件（护照/签证/LOA 等）",
                    "urgent": False,
                }
            )
        start = e.expected_start
        if start and 0 <= (start - today).days <= ARRIVAL_SOON_DAYS:
            out.append(
                {
                    "kind": "临行入学",
                    "student_no": s.student_no,
                    "student_name": s.name,
                    "detail": f"{p.name}｜{(start - today).days} 天后入学（{start.isoformat()}）",
                    "urgent": True,
                }
            )
    order = {"临行入学": 0, "报价跟进": 1, "待报价跟进": 2, "材料收集中": 3}
    out.sort(key=lambda x: (not x["urgent"], order.get(x["kind"], 9)))
    return out


def overview(session: Session) -> dict:
    agency = get_agency(session)
    warnings: list[dict] = []

    agency_dict = None
    if agency is None:
        warnings.append({"level": "error", "code": "AGENCY_MISSING", "message": "尚未建立机构合规档案"})
    else:
        agency_dict = {
            "id": agency.id,
            "name": agency.name,
            "uscc": agency.uscc,
            "travel_license_no": agency.travel_license_no,
            "outbound_licensed": agency.outbound_licensed,
            "license_expiry": agency.license_expiry.isoformat() if agency.license_expiry else None,
            "filing_status": agency.filing_status,
            "filing_no": agency.filing_no,
            "filing_date": agency.filing_date.isoformat() if agency.filing_date else None,
            "premise_proof": agency.premise_proof,
            "policy_documents": agency.policy_documents,
        }
        if agency.filing_status != "已备案":
            warnings.append(
                {
                    "level": "warning",
                    "code": "EXIT_ENTRY_FILING_PENDING",
                    "message": "841号令出入境中介备案未完成（存量机构须于2026-12-15前办理）",
                }
            )
        expiry = agency.license_expiry
        if isinstance(expiry, date):
            if expiry < date.today():
                warnings.append({"level": "error", "code": "LICENSE_EXPIRED", "message": "旅行社业务经营许可证已过期"})
            elif expiry <= date.today() + timedelta(days=90):
                warnings.append({"level": "warning", "code": "LICENSE_EXPIRING", "message": "旅行社业务经营许可证90天内到期"})

    staff_rows = []
    for s in session.scalars(select(Staff)).all():
        staff_rows.append(
            {
                "id": s.id,
                "name": s.name,
                "role": s.role,
                "no_crime_declaration": s.no_crime_declaration,
                "filing_status": s.filing_status,
                "filing_date": s.filing_date.isoformat() if s.filing_date else None,
                "expiry_date": s.expiry_date.isoformat() if s.expiry_date else None,
            }
        )
        if s.filing_status != "已备案":
            warnings.append(
                {"level": "warning", "code": "STAFF_FILING_PENDING", "message": f"备案人员「{s.name}」尚未完成人员备案"}
            )

    programs_at_risk = []
    for p in session.scalars(select(Program)).all():
        violations = cpl.check_program(
            program_check_data(session, cpl.program_to_dict(p)), cpl.agency_to_dict(agency)
        )
        errors = [v for v in violations if v["level"] == "error"]
        if errors:
            programs_at_risk.append({"id": p.id, "name": p.name, "violations": errors})

    return {
        "agency": agency_dict,
        "staff": staff_rows,
        "warnings": warnings,
        "programs_at_risk": programs_at_risk,
        "business": _business_stats(session),
        "funnel": _funnel(session),
        "expiring_documents": _expiring_documents(session),
        "follow_ups": _follow_ups(session),
        "audit_chain": verify_chain(session),
    }
