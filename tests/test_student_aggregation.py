"""学员主索引归集测试：按 student_no 找到该学员全部记录。"""


def _seed_world(session):
    from app.services import crud_helpers as ch

    agency = ch.create_agency(session, {
        "name": "示例游学服务有限公司",
        "uscc": "91370000DEMO00001X",
        "travel_license_no": "L-SD-DEMO001",
        "outbound_licensed": True,
    })
    student = ch.create_student(session, {
        "student_no": "STU-2026-001",
        "name": "学员甲",
        "birth_date": "2012-05-01",
        "guardian_name": "监护甲",
        "guardian_phone": "13800000000",
    })
    program = ch.create_program(session, {
        "name": "寒假游学营（虚构）",
        "type": "出境游学",
        "departure_date": "2027-01-20",
        "return_date": "2027-02-02",
        "filing_date": "2026-12-01",
        "filing_status": "已备案",
        "status": "筹备中",
        "dest_country_count": 1,
        "max_cities_per_country": 3,
        "student_age_group": "中学",
        "teacher_count": 2,
        "student_count": 16,
        "insurance": {"policy_no": "INS-001", "coverage_per_person_wan": 80,
                      "coverage_per_accident_wan": 1200, "includes_global_rescue": True},
        "emergency_plan": True,
        "partner_school": "境外合作学校（虚构）", "school_verified": True,
    })
    ch.create_consent(session, {"student_id": student.id, "program_id": program.id,
                                "consent_type": "敏感信息处理", "individual_consent": True,
                                "signer_name": "监护甲", "relation": "母亲"})
    ch.create_document(session, {"student_id": student.id, "doc_type": "护照",
                                 "doc_no": "E12345678（虚构）", "expiry_date": "2030-09-01"})
    # 出发日（2027-01-20）学员未满 15 周岁 → 按 WEG 规则先登记监护同行证明
    ch.create_document(session, {"student_id": student.id, "doc_type": "监护同行证明",
                                 "doc_no": "同行-2026-001（虚构）"})
    ch.create_enrollment(session, {"student_id": student.id, "program_id": program.id,
                                   "health_proof": True, "parent_notice_signed": True})
    contract = ch.create_contract(session, {
        "contract_no": "CT-2026-001",
        "student_id": student.id,
        "service_scope": ["留学方案咨询", "院校申请"],
        "total_fee": "30000",
        "signed_date": "2026-11-01",
        "refund_rules": [{"stage": "未递交材料", "ratio": "100"}],
        "status": "履行中",
    })
    ch.create_payment(session, {"contract_id": contract.id, "type": "服务费",
                                "amount": "15000", "voucher_no": "V-001",
                                "payee": "示例游学服务有限公司"})
    ch.create_service_event(session, {"student_id": student.id, "contract_id": contract.id,
                                      "event_type": "材料递交", "occurred_at": "2026-11-10T10:00:00",
                                      "operator": "顾问乙"})
    return student


def test_collect_returns_all_record_types(session):
    from app.services.aggregation import collect_student_records

    student = _seed_world(session)
    data = collect_student_records(session, student.student_no)

    assert data["student"]["student_no"] == "STU-2026-001"
    assert len(data["enrollments"]) == 1 and data["enrollments"][0]["program_name"]
    assert len(data["contracts"]) == 1 and data["contracts"][0]["payments"]
    assert len(data["service_events"]) == 1
    assert len(data["consents"]) == 1
    # 归集自带审计溯源计数
    assert data["audit_count"] >= 1


def test_collect_unknown_student_raises_404_style(session):
    import pytest

    from app.services.aggregation import StudentNotFound, collect_student_records

    with pytest.raises(StudentNotFound):
        collect_student_records(session, "NO-SUCH-STUDENT")


def test_orphan_student_has_empty_lists(session):
    from app.services import crud_helpers as ch
    from app.services.aggregation import collect_student_records

    ch.create_student(session, {"student_no": "STU-2026-002", "name": "学员乙",
                                "birth_date": "2000-01-01"})
    data = collect_student_records(session, "STU-2026-002")
    assert data["contracts"] == [] and data["consents"] == []
    assert data["is_minor"] is False
