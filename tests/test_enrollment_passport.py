"""出境游学报名的护照有效期校验（≥行程结束后6个月）。"""
import pytest


def _setup(session, client, passport_expiry=None):
    from app.services import crud_helpers as ch

    ch.create_agency(session, {
        "name": "示例游学服务有限公司", "uscc": "91370000DEMO00001X",
        "travel_license_no": "L-SD-DEMO001", "outbound_licensed": True,
    })
    program_id = client.post("/api/programs", json={
        "name": "出境营（虚构）", "type": "出境游学",
        "departure_date": "2027-01-20", "return_date": "2027-02-02",
        "filing_date": "2026-12-01", "filing_status": "已备案", "status": "筹备中",
        "dest_country_count": 1, "max_cities_per_country": 2,
        "student_age_group": "中学", "teacher_count": 2, "student_count": 16,
        "insurance": {"policy_no": "INS-001", "coverage_per_person_wan": 80,
                      "coverage_per_accident_wan": 1200, "includes_global_rescue": True},
        "emergency_plan": True,
        "partner_school": "境外学校（虚构）", "school_verified": True,
    }).json()["id"]
    student = ch.create_student(session, {
        "student_no": "STU-2030-001", "name": "成年学员（虚构）", "birth_date": "2000-01-01",
    })
    ch.create_consent(session, {
        "student_id": student.id, "program_id": program_id,
        "consent_type": "敏感信息处理", "individual_consent": True,
        "signer_name": "本人", "relation": "本人",
    })
    if passport_expiry:
        ch.create_document(session, {
            "student_id": student.id, "doc_type": "护照",
            "doc_no": "E88888888（虚构）", "expiry_date": passport_expiry,
        })
    return student, program_id


def test_enroll_outbound_without_passport_blocked(client, session):
    student, program_id = _setup(session, client)
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
        "health_proof": True, "parent_notice_signed": True,
    })
    assert r.status_code == 422
    assert "PASSPORT" in r.json()["detail"]


def test_enroll_outbound_with_short_passport_blocked(client, session):
    # 行程结束 2027-02-02 → 须有效至 2027-08-02 之后；2027-08-01 差一天
    student, program_id = _setup(session, client, passport_expiry="2027-08-01")
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
        "health_proof": True, "parent_notice_signed": True,
    })
    assert r.status_code == 422
    assert "PASSPORT_INVALID" in r.json()["detail"]


def test_enroll_outbound_with_valid_passport_ok(client, session):
    student, program_id = _setup(session, client, passport_expiry="2027-09-01")
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
        "health_proof": True, "parent_notice_signed": True,
    })
    assert r.status_code == 201


def test_domestic_enroll_needs_no_passport(client, session):
    from app.services import crud_helpers as ch

    ch.create_agency(session, {
        "name": "示例游学服务有限公司", "uscc": "91370000DEMO00001X",
        "travel_license_no": "L-SD-DEMO001", "outbound_licensed": True,
    })
    program_id = client.post("/api/programs", json={
        "name": "境内营（虚构）", "type": "境内研学",
        "departure_date": "2027-04-10", "return_date": "2027-04-12",
        "filing_date": "2027-03-01", "filing_status": "已备案", "status": "筹备中",
        "student_age_group": "中学", "teacher_count": 1, "student_count": 8,
        "insurance": None, "emergency_plan": False,
    }).json()["id"]
    student = ch.create_student(session, {
        "student_no": "STU-2030-002", "name": "成年学员乙（虚构）", "birth_date": "2000-01-01",
    })
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
        "health_proof": True, "parent_notice_signed": True,
    })
    assert r.status_code == 201


def test_update_audit_has_before_after(session):
    from sqlalchemy import select

    from app.models import AuditLog
    from app.services import crud_helpers as ch

    agency = ch.create_agency(session, {"name": "旧名（虚构）", "uscc": "U1"})
    ch.update_agency(session, {"name": "新名（虚构）"})
    log = session.scalars(
        select(AuditLog).where(AuditLog.action == "update", AuditLog.entity == "agency")
        .order_by(AuditLog.id.desc())
    ).first()
    assert log.payload["before"]["name"] == "旧名（虚构）"
    assert log.payload["after"]["name"] == "新名（虚构）"
