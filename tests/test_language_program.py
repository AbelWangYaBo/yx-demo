"""语言研修（个人计划型 Program）：校验分支 + 护照适用 + 免备案。"""


def _world(session, client):
    from app.services import crud_helpers as ch

    ch.create_agency(session, {"name": "示例远航游学（虚构）", "uscc": "U-LANG", "outbound_licensed": True})
    school = ch.create_school(session, {
        "name": "SMEAG（虚构演示）", "region": "宿务", "style": "半斯巴达",
        "commission_rate": "20", "registration_fee_usd": "100", "verified": True,
    })
    course = ch.create_course(session, {
        "school_id": school.id, "name": "ESL 一般英文", "course_type": "ESL",
        "lessons": "1对1×4 + 团体×2 + 选修×4", "min_weeks": 4,
        "room_prices": {"4人间": 180, "3人间": 205, "2人间": 240, "1人间": 310},
    })
    student = ch.create_student(session, {
        "student_no": "STU-LANG-001", "name": "研修学员（虚构）", "birth_date": "2001-06-01",
    })
    return school, course, student


def _lang_program_payload(school, course, **over):
    payload = {
        "name": f"{school['name'] if isinstance(school, dict) else school.name}·ESL 8周（虚构）",
        "type": "语言研修",
        "departure_date": "2027-02-07", "return_date": "2027-04-03",  # 8周：+56-1
        "school_id": school["id"] if isinstance(school, dict) else school.id,
        "course_id": course["id"] if isinstance(course, dict) else course.id,
        "weeks": 8, "room_type": "2人间",
    }
    payload.update(over)
    return payload


def _violation_codes(r):
    return {v["code"] for v in r.json()["detail"]["violations"]}


def test_language_program_weeks_below_min_blocked(client, session):
    school, course, _ = _world(session, client)
    r = client.post("/api/programs", json=_lang_program_payload(school, course, weeks=2))
    assert r.status_code == 422
    assert "WEEKS_BELOW_MIN" in _violation_codes(r)


def test_language_program_invalid_room_blocked(client, session):
    school, course, _ = _world(session, client)
    r = client.post("/api/programs", json=_lang_program_payload(school, course, room_type="总统套房"))
    assert r.status_code == 422
    assert "ROOM_TYPE_INVALID" in _violation_codes(r)


def test_language_program_requires_school_and_course(client, session):
    _, _, _ = _world(session, client)
    r = client.post("/api/programs", json={
        "name": "缺学校的研修（虚构）", "type": "语言研修",
        "departure_date": "2027-02-07", "return_date": "2027-03-06",
        "weeks": 4, "room_type": "4人间",
    })
    assert r.status_code == 422
    assert "LANG_SCHOOL_REQUIRED" in _violation_codes(r)


def test_language_program_no_filing_required(client, session):
    """个人语言研修不是研学团：不要求备案/师生比/应急预案（保险仅提示）。"""
    school, course, _ = _world(session, client)
    r = client.post("/api/programs", json=_lang_program_payload(school, course))
    assert r.status_code == 201, r.text
    prog = r.json()
    assert prog["filing_status"] == "未备案"  # 不因未备案被拦
    assert prog["weeks"] == 8


def test_language_program_enrollment_needs_passport(client, session):
    """语言研修也是出境：报名同样要求护照有效至离校后6个月。"""
    from app.services import crud_helpers as ch

    school, course, student = _world(session, client)
    program_id = client.post("/api/programs", json=_lang_program_payload(school, course)).json()["id"]
    # 无护照 → 拦截
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
    })
    assert r.status_code == 422
    assert "PASSPORT_REQUIRED" in r.json()["detail"]
    # 离校 2027-04-03 → 须有效至 2027-10-03
    ch.create_document(session, {
        "student_id": student.id, "doc_type": "护照",
        "doc_no": "E91000001（虚构）", "expiry_date": "2027-10-02",
    })
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
    })
    assert r.status_code == 422  # 差一天也不行
    assert "PASSPORT_INVALID" in r.json()["detail"]
    # 换发新护照（有效至 2028）后放行
    ch.create_document(session, {
        "student_id": student.id, "doc_type": "护照",
        "doc_no": "E91000001N（虚构）", "expiry_date": "2028-06-30",
    })
    r = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
    })
    assert r.status_code == 201


def test_direct_language_enrollment_creates_program(client, session):
    """报名接口直建模式：带课程参数、不带 program_id → 事务内先建研修计划再报名。"""
    school, course, student = _world(session, client)
    from app.services import crud_helpers as ch

    ch.create_document(session, {
        "student_id": student.id, "doc_type": "护照",
        "doc_no": "E91000002（虚构）", "expiry_date": "2031-01-01",
    })
    r = client.post("/api/enrollments", json={
        "student_id": student.id,
        "school_id": school.id, "course_id": course.id,
        "weeks": 4, "room_type": "4人间", "start_date": "2027-02-07",
        "health_proof": True,
    })
    assert r.status_code == 201, r.text
    enr = r.json()
    assert enr["program_id"] and enr["course_name"] == "ESL 一般英文"
    assert enr["accommodation"] == "4人间"
    assert enr["expected_start"] == "2027-02-07"
    # return_date = 入学 + 4×7 - 1
    from sqlalchemy import select

    from app.models import Program
    prog = session.get(Program, enr["program_id"])
    assert str(prog.return_date) == "2027-03-06"
