"""业务管线：学员生命周期 + 报名执行阶段的推进与拦截。"""
import pytest


def _world(session, client, outbound=True):
    from app.services import crud_helpers as ch

    ch.create_agency(session, {
        "name": "示例游学服务有限公司", "uscc": "U-DEMO-P", "outbound_licensed": True,
    })
    program = {
        "name": "管线测试营（虚构）", "type": "出境游学" if outbound else "境内研学",
        "departure_date": "2027-07-01", "return_date": "2027-07-10",
        "filing_date": "2027-05-01", "filing_status": "已备案", "status": "筹备中",
        "student_age_group": "中学", "teacher_count": 2, "student_count": 10,
        "emergency_plan": True,
        "partner_school": "境外学校（虚构）" if outbound else None,
        "school_verified": True if outbound else None,
    }
    if outbound:
        program["dest_country_count"] = 1
        program["max_cities_per_country"] = 2
        program["insurance"] = {"policy_no": "INS-P", "coverage_per_person_wan": 80,
                                "coverage_per_accident_wan": 1200, "includes_global_rescue": True}
    program_id = client.post("/api/programs", json=program).json()["id"]

    student = ch.create_student(session, {
        "student_no": "STU-FLOW-001", "name": "流程学员（虚构）", "birth_date": "2000-01-01",
    })
    # 成年学员：无同意书依赖；出境报名仍需护照
    if outbound:
        ch.create_document(session, {"student_id": student.id, "doc_type": "护照",
                                     "doc_no": "E77777777（虚构）", "expiry_date": "2035-01-01"})
    enr = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
        "health_proof": True, "parent_notice_signed": True,
        "course_name": "语言强化课程（虚构）", "accommodation": "寄宿家庭（虚构）",
        "pickup_arranged": True, "expected_start": "2027-07-01",
    })
    assert enr.status_code == 201, enr.text
    return student, enr.json()


def test_enrollment_default_stage_and_fields(client, session):
    _, enr = _world(session, client)
    assert enr["stage"] == "已报名"
    assert enr["course_name"] == "语言强化课程（虚构）"
    assert enr["accommodation"] == "寄宿家庭（虚构）"
    assert enr["pickup_arranged"] is True


def test_enrollment_stage_forward_progress(client, session):
    student, enr = _world(session, client)
    # 材料准备 → 已缴费（先登记缴费）
    r = client.post(f"/api/enrollments/{enr['id']}/stage",
                    json={"stage": "材料准备", "remark": "收齐护照机票"})
    assert r.status_code == 200 and r.json()["stage"] == "材料准备"
    r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "已缴费"})
    assert r.status_code == 200
    # 每次推进写服务节点 + 审计
    data = client.get(f"/api/students/{student.student_no}/records").json()
    nodes = [e for e in data["service_events"] if e["event_type"] == "阶段变更"]
    assert len(nodes) >= 2
    assert "材料准备" in nodes[0]["remark"]
    audit = client.get("/api/audit").json()["items"]
    assert any(a["action"] == "stage" for a in audit)


def test_enrollment_stage_backward_blocked(client, session):
    _, enr = _world(session, client)
    client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "材料准备"})
    r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "已报名"})
    assert r.status_code == 422


def test_enrollment_enter_school_requires_payment(client, session):
    _, enr = _world(session, client)
    # 跳过缴费直接入学 → 拦截
    r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "已入学"})
    assert r.status_code == 422
    assert "NEED_PAYMENT" in r.json()["detail"]
    # 正常路径：缴费后可入学
    contract = client.post("/api/contracts", json={
        "contract_no": "CT-FLOW-1", "student_id": enr["student_id"],
        "total_fee": "20000", "signed_date": "2026-11-17",
        "refund_rules": [{"stage": "未开始", "ratio": "100"}],
    }).json()
    client.post("/api/payments", json={
        "contract_id": contract["id"], "type": "服务费", "amount": "20000",
        "voucher_no": "V-FLOW-1", "payee": "示例游学服务有限公司",
    })
    r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "已入学"})
    assert r.status_code == 200


def test_unknown_stage_rejected(client, session):
    _, enr = _world(session, client)
    r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "飞行阶段"})
    assert r.status_code == 422
    assert "STAGE_UNKNOWN" in r.json()["detail"]


def test_same_stage_repeat_rejected(client, session):
    _, enr = _world(session, client)
    client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "材料准备"})
    r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "材料准备"})
    assert r.status_code == 422
    assert "STAGE_SAME" in r.json()["detail"]


def test_student_lifecycle_progress(client, session):
    student, _ = _world(session, client)
    for stage in ("沟通中", "已报名", "在读", "已毕业"):
        r = client.post(f"/api/students/{student.student_no}/stage", json={"stage": stage})
        assert r.status_code == 200, r.text
    assert client.get(f"/api/students/{student.student_no}").json()["stage"] == "已毕业"


def test_student_lifecycle_backward_blocked(client, session):
    student, _ = _world(session, client)
    client.post(f"/api/students/{student.student_no}/stage", json={"stage": "沟通中"})
    r = client.post(f"/api/students/{student.student_no}/stage", json={"stage": "意向"})
    assert r.status_code == 422


def test_student_lost_allowed_anytime(client, session):
    student, _ = _world(session, client)
    r = client.post(f"/api/students/{student.student_no}/stage", json={"stage": "已流失"})
    assert r.status_code == 200


def test_aggregation_contains_student_stage(client, session):
    student, _ = _world(session, client)
    client.post(f"/api/students/{student.student_no}/stage", json={"stage": "沟通中"})
    data = client.get(f"/api/students/{student.student_no}/records").json()
    assert data["student"]["stage"] == "沟通中"
