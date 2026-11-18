"""菲律宾行政链条：推进「在读」须 SSP；>59 天课程还须 ACR I-Card。"""


def _world(session, client, weeks=12):
    """成年学员 + 已缴费、已入学的语言研修报名。"""
    from app.services import crud_helpers as ch

    ch.create_agency(session, {"name": "示例远航游学（虚构）", "uscc": "U-PHC", "outbound_licensed": True})
    school = ch.create_school(session, {
        "name": "EV Academy（虚构演示）", "region": "宿务", "country": "菲律宾", "style": "斯巴达",
        "commission_rate": "25", "registration_fee_usd": "100", "verified": True,
    })
    course = ch.create_course(session, {
        "school_id": school.id, "name": "IELTS 保分班", "course_type": "IELTS保分",
        "lessons": "1对1×4 + 团体×3", "min_weeks": 12,
        "room_prices": {"4人间": 310, "3人间": 330, "2人间": 365, "1人间": 430},
    })
    student = ch.create_student(session, {
        "student_no": "STU-PHC-001", "name": "链条学员（虚构）", "birth_date": "2000-01-01",
    })
    ch.create_document(session, {
        "student_id": student.id, "doc_type": "护照",
        "doc_no": "E92000001（虚构）", "expiry_date": "2033-01-01",
    })
    enr = client.post("/api/enrollments", json={
        "student_id": student.id,
        "school_id": school.id, "course_id": course.id,
        "weeks": weeks, "room_type": "4人间", "start_date": "2026-09-13",
    }).json()
    contract = client.post("/api/contracts", json={
        "contract_no": "CT-PHC-1", "student_id": student.id,
        "total_fee": "3820", "signed_date": "2026-08-01",
        "refund_rules": [{"stage": "开课前2-4周取消", "ratio": "70"}],
    }).json()
    client.post("/api/payments", json={
        "contract_id": contract["id"], "type": "代收代缴-学费", "amount": "3820",
        "currency": "USD", "voucher_no": "V-PHC-1", "payee": "EV Academy（虚构）",
    })
    client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "材料准备"})
    client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "已缴费"})
    client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "已入学"})
    return student, enr


def _register_doc(session, student_id, doc_type):
    from app.services import crud_helpers as ch

    ch.create_document(session, {
        "student_id": student_id, "doc_type": doc_type,
        "doc_no": f"{doc_type}-NO（虚构）",
    })


def test_advance_to_study_requires_ssp(client, session):
    student, enr = _world(session, client)
    r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "在读"})
    assert r.status_code == 422
    assert "SSP_REQUIRED" in r.json()["detail"]


def test_long_course_requires_acr_too(client, session):
    """12 周 = 84 天 > 59 天：有 SSP 无 ACR 仍被拦。"""
    student, enr = _world(session, client, weeks=12)
    _register_doc(session, student.id, "SSP")
    r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "在读"})
    assert r.status_code == 422
    assert "ACR_REQUIRED" in r.json()["detail"]
    # 补 ACR 后放行
    _register_doc(session, student.id, "ACR I-Card")
    r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": "在读"})
    assert r.status_code == 200, r.text


def test_short_course_no_acr_needed(client, session):
    """8 周 = 56 天 ≤ 59 天：SSP 即可，ACR 不要求。"""
    school_course = None  # 世界按 12 周建；此处单独建 8 周场景
    student, enr = _world(session, client, weeks=12)
    # 另建一个 8 周学员（SMEAG ESL 无最短 12 周限制）
    from app.services import crud_helpers as ch

    if school_course is None:
        school = ch.create_school(session, {
            "name": "SMEAG（虚构演示）", "region": "宿务", "country": "菲律宾",
            "style": "半斯巴达", "commission_rate": "20",
            "registration_fee_usd": "100", "verified": True,
        })
        course = ch.create_course(session, {
            "school_id": school.id, "name": "ESL 一般英文", "course_type": "ESL",
            "min_weeks": 4, "room_prices": {"4人间": 180, "2人间": 240},
        })
        student2 = ch.create_student(session, {
            "student_no": "STU-PHC-002", "name": "短课学员（虚构）", "birth_date": "1999-01-01",
        })
        ch.create_document(session, {
            "student_id": student2.id, "doc_type": "护照",
            "doc_no": "E92000002（虚构）", "expiry_date": "2033-01-01",
        })
        enr2 = client.post("/api/enrollments", json={
            "student_id": student2.id,
            "school_id": school.id, "course_id": course.id,
            "weeks": 8, "room_type": "4人间", "start_date": "2026-09-13",
        }).json()
        contract = client.post("/api/contracts", json={
            "contract_no": "CT-PHC-2", "student_id": student2.id,
            "total_fee": "1540", "signed_date": "2026-08-01",
            "refund_rules": [{"stage": "开课前2-4周取消", "ratio": "70"}],
        }).json()
        client.post("/api/payments", json={
            "contract_id": contract["id"], "type": "代收代缴-学费",
            "amount": "1540", "currency": "USD",
            "voucher_no": "V-PHC-2", "payee": "SMEAG（虚构演示）",
        })
        for stage in ("材料准备", "已缴费", "已入学"):
            client.post(f"/api/enrollments/{enr2['id']}/stage", json={"stage": stage})
        _register_doc(session, student2.id, "SSP")
        r = client.post(f"/api/enrollments/{enr2['id']}/stage", json={"stage": "在读"})
        assert r.status_code == 200, r.text


def test_group_program_not_checked_for_ssp(client, session):
    """团体营（出境游学，非语言研修）不做 SSP/ACR 拦截。"""
    from app.services import crud_helpers as ch

    ch.create_agency(session, {"name": "示例远航游学（虚构）", "uscc": "U-PHC-G", "outbound_licensed": True})
    program_id = client.post("/api/programs", json={
        "name": "新加坡营（虚构）", "type": "出境游学",
        "departure_date": "2027-01-20", "return_date": "2027-02-02",
        "filing_date": "2026-12-01", "filing_status": "已备案",
        "dest_country_count": 1, "max_cities_per_country": 2,
        "student_age_group": "中学", "teacher_count": 2, "student_count": 16,
        "insurance": {"policy_no": "INS-01", "coverage_per_person_wan": 80,
                      "coverage_per_accident_wan": 1200, "includes_global_rescue": True},
        "emergency_plan": True, "partner_school": "境外学校（虚构）", "school_verified": True,
    }).json()["id"]
    student = ch.create_student(session, {
        "student_no": "STU-PHC-003", "name": "团体学员（虚构）", "birth_date": "2000-01-01",
    })
    ch.create_document(session, {
        "student_id": student.id, "doc_type": "护照",
        "doc_no": "E92000003（虚构）", "expiry_date": "2033-01-01",
    })
    enr = client.post("/api/enrollments", json={
        "student_id": student.id, "program_id": program_id,
    }).json()
    contract = client.post("/api/contracts", json={
        "contract_no": "CT-PHC-3", "student_id": student.id,
        "total_fee": "10000", "signed_date": "2026-11-01",
        "refund_rules": [{"stage": "未开始", "ratio": "100"}],
    }).json()
    client.post("/api/payments", json={
        "contract_id": contract["id"], "type": "服务费", "amount": "10000",
        "voucher_no": "V-PHC-3", "payee": "示例远航游学（虚构）",
    })
    for stage in ("材料准备", "已缴费", "已入学", "在读"):
        r = client.post(f"/api/enrollments/{enr['id']}/stage", json={"stage": stage})
        assert r.status_code == 200, r.text  # 无 SSP 也直接放行
