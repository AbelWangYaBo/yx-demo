"""学员主索引归集：按 student_no 找到该学员在机构下的全部记录。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Attachment,
    AuditLog,
    CommunicationLog,
    Consent,
    Contract,
    Course,
    Enrollment,
    Payment,
    Program,
    Quotation,
    School,
    ServiceEvent,
    Student,
    StudentDocument,
    WeeklyReport,
)
from app.services.common import is_minor
from app.services.errors import StudentNotFound


def _iso(value):
    return value.isoformat() if value is not None else None


def _student_dict(student: Student) -> dict:
    return {
        "id": student.id,
        "student_no": student.student_no,
        "name": student.name,
        "birth_date": _iso(student.birth_date),
        "stage": student.stage,
        "guardian_name": student.guardian_name,
        "guardian_phone": student.guardian_phone,
        "guardian_id_masked": student.guardian_id_masked,
        "notes": student.notes,
    }


def collect_student_records(session: Session, student_no: str) -> dict:
    student = session.scalars(select(Student).where(Student.student_no == student_no)).first()
    if student is None:
        raise StudentNotFound(f"学员不存在: {student_no}")

    enrollments = []
    for e in session.scalars(select(Enrollment).where(Enrollment.student_id == student.id)).all():
        program = session.get(Program, e.program_id)
        school = session.get(School, program.school_id) if program and program.school_id else None
        course = session.get(Course, program.course_id) if program and program.course_id else None
        reports = session.scalars(
            select(WeeklyReport).where(WeeklyReport.enrollment_id == e.id)
            .order_by(WeeklyReport.week_no)
        ).all()
        enrollments.append(
            {
                "id": e.id,
                "program_id": e.program_id,
                "program_name": program.name if program else None,
                "program_type": program.type if program else None,
                "school_name": school.name if school else None,
                "school_country": school.country if school else None,
                "course_name": e.course_name or (course.name if course else None),
                "accommodation": e.accommodation,
                "pickup_arranged": e.pickup_arranged,
                "expected_start": _iso(e.expected_start),
                "weeks": program.weeks if program else None,
                "room_type": program.room_type if program else None,
                "stage": e.stage,
                "quotation_id": e.quotation_id,
                "health_proof": e.health_proof,
                "parent_notice_signed": e.parent_notice_signed,
                "created_at": _iso(e.created_at),
                "weekly_reports": [
                    {
                        "id": r.id,
                        "week_no": r.week_no,
                        "level": r.level,
                        "test_score": r.test_score,
                        "attendance_pct": r.attendance_pct,
                        "teacher_comment": r.teacher_comment,
                        "parent_notified_at": _iso(r.parent_notified_at),
                    }
                    for r in reports
                ],
            }
        )

    quotations = []
    for q in session.scalars(
        select(Quotation).where(Quotation.student_id == student.id).order_by(Quotation.id)
    ).all():
        school = session.get(School, q.school_id)
        course = session.get(Course, q.course_id)
        quotations.append(
            {
                "id": q.id,
                "quote_no": q.quote_no,
                "school_id": q.school_id,
                "course_id": q.course_id,
                "school_name": school.name if school else None,
                "course_name": course.name if course else None,
                "weeks": q.weeks,
                "room_type": q.room_type,
                "start_date": _iso(q.start_date),
                "items": q.items,
                "total_usd": q.total_usd,
                "status": q.status,
                "created_at": _iso(q.created_at),
            }
        )

    contracts = []
    for c in session.scalars(select(Contract).where(Contract.student_id == student.id)).all():
        payment_rows = session.scalars(select(Payment).where(Payment.contract_id == c.id)).all()
        payments = [
            {
                "id": p.id,
                "type": p.type,
                "amount": p.amount,
                "currency": p.currency,
                "voucher_no": p.voucher_no,
                "payee": p.payee,
                "proof_file": p.proof_file,
                "paid_at": _iso(p.paid_at),
            }
            for p in payment_rows
        ]
        from app.services.finance import contract_settlement

        contracts.append(
            {
                "id": c.id,
                "contract_no": c.contract_no,
                "service_scope": c.service_scope,
                "total_fee": c.total_fee,
                "currency": c.currency,
                "signed_date": _iso(c.signed_date),
                "refund_rules": c.refund_rules,
                "status": c.status,
                "settlement": contract_settlement(c.total_fee, c.currency, payment_rows),
                "payments": payments,
            }
        )

    service_events = [
        {
            "id": ev.id,
            "contract_id": ev.contract_id,
            "event_type": ev.event_type,
            "occurred_at": _iso(ev.occurred_at),
            "operator": ev.operator,
            "remark": ev.remark,
        }
        for ev in session.scalars(
            select(ServiceEvent).where(ServiceEvent.student_id == student.id).order_by(ServiceEvent.occurred_at)
        ).all()
    ]

    consents = [
        {
            "id": c.id,
            "consent_type": c.consent_type,
            "individual_consent": c.individual_consent,
            "signer_name": c.signer_name,
            "relation": c.relation,
            "status": c.status,
            "signed_at": _iso(c.signed_at),
            "revoked_at": _iso(c.revoked_at),
        }
        for c in session.scalars(select(Consent).where(Consent.student_id == student.id)).all()
    ]

    # 审计溯源：entity_id 直接命中 + payload 引用该学员的日志
    audit_count = 0
    for log in session.scalars(select(AuditLog)).all():
        if log.entity_id == student_no or (log.payload or {}).get("student_no") == student_no:
            audit_count += 1

    documents = []
    for d in session.scalars(select(StudentDocument).where(StudentDocument.student_id == student.id)).all():
        att = session.get(Attachment, d.attachment_id) if d.attachment_id else None
        documents.append(
            {
                "id": d.id,
                "doc_type": d.doc_type,
                "doc_no": d.doc_no,
                "issued_date": _iso(d.issued_date),
                "expiry_date": _iso(d.expiry_date),
                "file_ref": d.file_ref,
                "attachment_id": d.attachment_id,
                "attachment_filename": att.filename if att else None,
                "remark": d.remark,
            }
        )

    communications = [
        {
            "id": m.id,
            "channel": m.channel,
            "direction": m.direction,
            "occurred_at": _iso(m.occurred_at),
            "operator": m.operator,
            "summary": m.summary,
        }
        for m in session.scalars(
            select(CommunicationLog)
            .where(CommunicationLog.student_id == student.id)
            .order_by(CommunicationLog.occurred_at.desc())
        ).all()
    ]

    return {
        "student": _student_dict(student),
        "is_minor": is_minor(student.birth_date),
        "enrollments": enrollments,
        "quotations": quotations,
        "contracts": contracts,
        "service_events": service_events,
        "consents": consents,
        "documents": documents,
        "communications": communications,
        "audit_count": audit_count,
    }
