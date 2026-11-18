"""WEG（未满15岁出境）与在读周报。"""


def _outbound_world(session, client):
    from app.services import crud_helpers as ch

    ch.create_agency(session, {"name": "示例远航游学（虚构）", "uscc": "U-WEG", "outbound_licensed": True})
    program_id = client.post("/api/programs", json={
        "name": "寒假宿务冬令营（虚构）", "type": "出境游学",
        "departure_date": "2027-01-17", "return_date": "2027-02-06",
        "filing_date": "2026-12-10", "filing_status": "已备案",
        "dest_country_count": 1, "max_cities_per_country": 2,
        "student_age_group": "小学", "teacher_count": 2, "student_count": 16,
        "insurance": {"policy_no": "INS-W", "coverage_per_person_wan": 80,
                      "coverage_per_accident_wan": 1200, "includes_global_rescue": True},
        "emergency_plan": True, "partner_school": "CIA（虚构演示）", "school_verified": True,
    }).json()["id"]
    return program_id


def _minor(session, birth="2013-06-01", no="STU-WEG-001"):
    from app.services import crud_helpers as ch

    student = ch.create_student(session, {
        "student_no": no, "name": "未成年学员（虚构）", "birth_date": birth,
        "guardian_name": "家长（虚构）",
    })
    ch.create_document(session, {
        "student_id": student.id, "doc_type": "护照",
        "doc_no": "E93000001（虚构）", "expiry_date": "2032-01-01",
    })
    return student


def test_under_15_outbound_without_weg_blocked(client, session):
    """出发日 2027-01-17 时 13 岁 → 无 WEG/监护同行证明，拦截。"""
    program_id = _outbound_world(session, client)
    student = _minor(session, birth="2013-06-01")
    from app.services import crud_helpers as ch

    ch.create_consent(session, {
        "student_id": student.id, "program_id": program_id,
        "consent_type": "敏感信息处理", "individual_consent": True,
        "signer_name": "家长（虚构）", "relation": "母亲",
    })
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
        "health_proof": True, "parent_notice_signed": True,
    })
    assert r.status_code == 422
    assert "WEG_REQUIRED" in r.json()["detail"]


def test_under_15_with_weg_passes(client, session):
    program_id = _outbound_world(session, client)
    student = _minor(session, birth="2013-06-01", no="STU-WEG-002")
    from app.services import crud_helpers as ch

    ch.create_consent(session, {
        "student_id": student.id, "program_id": program_id,
        "consent_type": "敏感信息处理", "individual_consent": True,
        "signer_name": "家长（虚构）", "relation": "母亲",
    })
    ch.create_document(session, {
        "student_id": student.id, "doc_type": "WEG",
        "doc_no": "WEG-2027-001（虚构）", "remark": "领队统一办理（虚构）",
    })
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
        "health_proof": True, "parent_notice_signed": True,
    })
    assert r.status_code == 201, r.text


def test_under_15_with_guardian_companion_passes(client, session):
    """亲子课程：家长同行 → 监护同行证明同样放行。"""
    program_id = _outbound_world(session, client)
    student = _minor(session, birth="2013-06-01", no="STU-WEG-003")
    from app.services import crud_helpers as ch

    ch.create_consent(session, {
        "student_id": student.id, "program_id": program_id,
        "consent_type": "敏感信息处理", "individual_consent": True,
        "signer_name": "家长（虚构）", "relation": "母亲",
    })
    ch.create_document(session, {
        "student_id": student.id, "doc_type": "监护同行证明",
        "doc_no": "同行-2027-001（虚构）", "remark": "母亲同校 Family 课程",
    })
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
    })
    assert r.status_code == 201, r.text


def test_age_15_plus_no_weg_needed(client, session):
    """出发日 2027-01-17 时满 15 岁（2011-06-01 出生）→ 不要求 WEG。"""
    program_id = _outbound_world(session, client)
    student = _minor(session, birth="2011-06-01", no="STU-WEG-004")  # 15.6 岁
    from app.services import crud_helpers as ch

    ch.create_consent(session, {
        "student_id": student.id, "program_id": program_id,
        "consent_type": "敏感信息处理", "individual_consent": True,
        "signer_name": "家长（虚构）", "relation": "母亲",
    })
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
    })
    assert r.status_code == 201, r.text


def test_weekly_report_crud_and_aggregation(client, session):
    from app.services import crud_helpers as ch

    program_id = _outbound_world(session, client)
    student = _minor(session, birth="2000-01-01", no="STU-WEG-005")
    enr = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
        "health_proof": True,
    }).json()
    # 分班测试（week 0）
    r = client.post("/api/weekly-reports", json={
        "enrollment_id": enr["id"], "week_no": 0, "level": "B1",
        "teacher_comment": "分班测试：中级班（虚构）",
        "parent_notified_at": "2026-09-14T20:00:00",
    })
    assert r.status_code == 201, r.text
    # 第1周周报
    r2 = client.post("/api/weekly-reports", json={
        "enrollment_id": enr["id"], "week_no": 1, "level": "B1",
        "test_score": "78", "attendance_pct": 100,
        "teacher_comment": "口语进步明显（虚构）",
    })
    assert r2.status_code == 201
    # 聚合进学员360（周报嵌在报名记录下）
    data = client.get(f"/api/students/{student.student_no}/records").json()
    reports = data["enrollments"][0]["weekly_reports"]
    assert len(reports) == 2
    assert reports[0]["week_no"] == 0
    assert reports[1]["test_score"] == "78"
    # 按 enrollment 过滤
    listed = client.get(f"/api/weekly-reports?enrollment_id={enr['id']}").json()
    assert len(listed) == 2
