"""核心 API 冒烟 + 合规拦截测试。"""
from app.services.crud_helpers import (
    create_agency,
    create_consent,
    create_student,
)

AGENCY = {
    "name": "示例游学服务有限公司",
    "uscc": "91370000DEMO00001X",
    "travel_license_no": "L-SD-DEMO001",
    "outbound_licensed": True,
    "filing_status": "已备案",
    "filing_no": "BA-2026-DEMO-001",
}

STUDENT = {
    "student_no": "STU-2027-100",
    "name": "学员丙",
    "birth_date": "2013-08-15",  # 未成年
    "guardian_name": "监护丙",
    "guardian_phone": "13900000000",
}

PROGRAM = {
    "name": "春季研学营（虚构）",
    "type": "境内研学",
    "departure_date": "2027-04-10",
    "return_date": "2027-04-14",
    "filing_date": "2027-03-01",
    "filing_status": "已备案",
    "status": "筹备中",
    "dest_country_count": None,
    "max_cities_per_country": None,
    "student_age_group": "中学",
    "teacher_count": 1,
    "student_count": 8,
    "insurance": None,
    "emergency_plan": False,
}


def test_full_flow_smoke(client, session):
    assert create_agency(session, AGENCY).id
    assert create_student(session, STUDENT).id
    r = client.get("/api/students")
    assert r.status_code == 200 and len(r.json()) >= 1

    # 写操作必须产生审计
    n0 = len(client.get("/api/audit").json()["items"])
    r = client.post("/api/students", json={
        "student_no": "STU-2027-101", "name": "学员丁",
        "birth_date": "2011-01-01", "guardian_name": "监护丁",
        "guardian_phone": "13700000000",
    })
    assert r.status_code == 201
    n1 = len(client.get("/api/audit").json()["items"])
    assert n1 == n0 + 1

    assert client.get("/api/audit/verify").json()["valid"] is True


def test_enroll_minor_without_consent_blocked(client, session):
    create_agency(session, AGENCY)
    s = create_student(session, STUDENT)
    r = client.post("/api/programs", json=PROGRAM)
    assert r.status_code == 201
    program_id = r.json()["id"]

    r = client.post("/api/enrollments", json={
        "student_id": s.id, "program_id": program_id,
        "health_proof": True, "parent_notice_signed": True,
    })
    assert r.status_code == 422
    assert "CONSENT" in r.json()["detail"]


def test_enroll_minor_with_consent_ok(client, session):
    create_agency(session, AGENCY)
    s = create_student(session, STUDENT)
    program_id = client.post("/api/programs", json=PROGRAM).json()["id"]
    create_consent(session, {
        "student_id": s.id, "program_id": program_id,
        "consent_type": "敏感信息处理", "individual_consent": True,
        "signer_name": "监护丙", "relation": "父亲",
    })
    r = client.post("/api/enrollments", json={
        "student_id": s.id, "program_id": program_id,
        "health_proof": True, "parent_notice_signed": True,
    })
    assert r.status_code == 201

    # 学员归集接口能看到该报名
    data = client.get(f"/api/students/{STUDENT['student_no']}/records").json()
    assert len(data["enrollments"]) == 1

    # 撤回同意后再次报名被拒
    consent_id = client.get("/api/consents").json()[0]["id"]
    r = client.post(f"/api/consents/{consent_id}/revoke")
    assert r.status_code == 200
    r = client.post("/api/enrollments", json={
        "student_id": s.id, "program_id": program_id + 1,  # 不同活动同样需要有效同意
        "health_proof": True, "parent_notice_signed": True,
    })
    assert r.status_code == 422


def test_program_patch_invalid_triggers_check(client, session):
    create_agency(session, AGENCY)
    r = client.post("/api/programs", json=PROGRAM)
    pid = r.json()["id"]
    # 改成未备案但已成团 → 校验失败
    bad = dict(PROGRAM, filing_status="未备案", filing_date=None, status="已成团")
    r = client.patch(f"/api/programs/{pid}", json=bad)
    assert r.status_code == 422


def test_compliance_overview_and_retention(client, session):
    create_agency(session, AGENCY)
    r = client.get("/api/compliance/overview")
    assert r.status_code == 200
    body = r.json()
    assert "agency" in body and "warnings" in body

    r = client.get("/api/meta/retention")
    rules = {x["key"]: x["years"] for x in r.json()["rules"]}
    assert rules["audit_log_years"] >= 1  # ≥6个月，按年取整
    assert rules["contract_years"] == 30
    assert rules["pia_years"] == 3
    assert rules["study_abroad_contract_years"] == 5


def test_student_404(client):
    assert client.get("/api/students/NOPE/records").status_code == 404


def test_agency_partial_patch_keeps_other_fields(client, session):
    from app.services.crud_helpers import create_agency

    create_agency(session, {"name": "示例机构（虚构）", "uscc": "U-DEMO-1",
                            "premise_proof": "旧合同.pdf"})
    r = client.patch("/api/agency", json={"premise_proof": "新合同.pdf"})
    assert r.status_code == 200
    assert r.json()["name"] == "示例机构（虚构）"  # 未提交字段不被清空
    assert r.json()["premise_proof"] == "新合同.pdf"

    # 审计含 before/after
    logs = client.get("/api/audit").json()["items"]
    upd = next(l for l in logs if l["action"] == "update" and l["entity"] == "agency")
    assert upd["payload"]["before"]["premise_proof"] == "旧合同.pdf"
    assert upd["payload"]["after"]["premise_proof"] == "新合同.pdf"
