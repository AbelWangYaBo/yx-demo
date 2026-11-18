"""证件材料与沟通记录测试（护照/签证/机票/报名表/学校材料/沟通记录）。"""


def _seed_student(session, student_no="STU-2028-001", birth_date="2010-05-01"):
    from app.services import crud_helpers as ch

    return ch.create_student(session, {
        "student_no": student_no, "name": "学员测试（虚构）", "birth_date": birth_date,
        "guardian_name": "监护人（虚构）", "guardian_phone": "13000000000",
    })


def test_create_passport_document(session):
    from app.services import crud_helpers as ch

    s = _seed_student(session)
    doc = ch.create_document(session, {
        "student_id": s.id, "doc_type": "护照", "doc_no": "E12345678（虚构）",
        "issued_date": "2024-01-01", "expiry_date": "2034-01-01",
        "file_ref": "护照复印件（虚构示例）.pdf",
    })
    assert doc.id and doc.doc_type == "护照"
    # 审计 payload 携带学员标识
    from sqlalchemy import select
    from app.models import AuditLog
    logs = session.scalars(select(AuditLog).where(AuditLog.entity == "document")).all()
    assert any(l.payload.get("student_no") == s.student_no for l in logs)


def test_aggregation_includes_documents_and_communications(session):
    from app.services import crud_helpers as ch
    from app.services.aggregation import collect_student_records

    s = _seed_student(session)
    ch.create_document(session, {
        "student_id": s.id, "doc_type": "机票", "doc_no": "MU567（虚构）",
        "issued_date": "2027-01-10",
    })
    ch.create_communication(session, {
        "student_id": s.id, "channel": "微信", "direction": "呼出",
        "occurred_at": "2026-11-17T10:00:00", "operator": "顾问乙（虚构）",
        "summary": "沟通游学行程安排（虚构）",
    })
    data = collect_student_records(session, s.student_no)
    assert len(data["documents"]) == 1 and data["documents"][0]["doc_type"] == "机票"
    assert len(data["communications"]) == 1 and data["communications"][0]["channel"] == "微信"


def test_passport_validity_helper(session):
    from datetime import date

    from app.services.enrollment_rules import passport_valid_until

    s = _seed_student(session)
    ch = __import__("app.services.crud_helpers", fromlist=["create_document"]).create_document
    ch(session, {
        "student_id": s.id, "doc_type": "护照", "doc_no": "E99999999（虚构）",
        "expiry_date": "2027-07-01",
    })
    # 行程 2027-01-10 结束 → +6个月 = 2027-07-10 > 2027-07-01 → 不足
    assert passport_valid_until(session, s.id) == date(2027, 7, 1)
