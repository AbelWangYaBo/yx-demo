"""财务对账（多币种折算）+ 总览业务看板（漏斗/材料预警/待办）+ 学员列表摘要。"""
import pytest


def test_fx_to_cny():
    from app.services.finance import fx_to_cny

    assert str(fx_to_cny("3820", "USD")) == "27504.00"
    assert str(fx_to_cny("58200", "PHP")) == "7275.00"
    assert str(fx_to_cny("3000", "CNY")) == "3000.00"
    with pytest.raises(ValueError):
        fx_to_cny("100", "JPY")


class _P:
    """缴费记录桩。"""

    def __init__(self, ptype, amount, currency):
        self.type = ptype
        self.amount = amount
        self.currency = currency


def test_contract_settlement_multi_currency():
    from app.services.finance import contract_settlement

    s = contract_settlement("3820", "USD", [
        _P("定金", "3000", "CNY"),
        _P("代收代缴-学费", "3720", "USD"),
        _P("代收代缴-注册费", "100", "USD"),
        _P("代收代缴-当地费", "58200", "PHP"),  # 不计入对账
    ])
    assert s["receivable_cny"] == "27504.00"
    assert s["paid_cny"] == "30504.00"  # 3000 + 3720×7.2 + 100×7.2
    assert s["cleared"] is True
    assert s["balance_cny"] == "-3000.00"
    assert s["local_fee_cny"] == "7275.00"


def test_contract_settlement_balance_owed():
    from app.services.finance import contract_settlement

    s = contract_settlement("2230", "USD", [_P("定金", "3000", "CNY")])
    assert s["cleared"] is False
    assert s["balance_cny"] == "13056.00"


def _board_world(session, client):
    """构建：在读学员 + 过期/临期材料 + 待跟进报价 + 临行入学。"""
    from datetime import date, timedelta

    from app.services import crud_helpers as ch
    from app.services.quotation import create_quotation

    ch.create_agency(session, {"name": "示例机构（虚构）", "uscc": "U-BOARD", "outbound_licensed": True})
    school = ch.create_school(session, {
        "name": "EV Academy（虚构演示）", "region": "宿务", "country": "菲律宾",
        "style": "斯巴达", "commission_rate": "25", "registration_fee_usd": "100",
    })
    course = ch.create_course(session, {
        "school_id": school.id, "name": "IELTS 保分班", "course_type": "IELTS保分",
        "min_weeks": 12, "room_prices": {"4人间": 310},
    })
    # 学员一：在读（SSP 10 天后到期 → 预警）
    s1 = ch.create_student(session, {"student_no": "STU-B-001", "name": "看板学员一（虚构）",
                                     "birth_date": "2000-01-01"})
    ch.create_document(session, {"student_id": s1.id, "doc_type": "护照",
                                 "doc_no": "E1", "expiry_date": "2035-01-01"})
    ch.create_document(session, {
        "student_id": s1.id, "doc_type": "SSP", "doc_no": "SSP-1",
        "expiry_date": (date.today() + timedelta(days=10)).isoformat(),
    })
    q1 = create_quotation(session, {
        "student_id": s1.id, "school_id": school.id, "course_id": course.id,
        "weeks": 12, "room_type": "4人间", "start_date": "2026-10-11", "status": "已发送",
    })
    from app.services.quotation import confirm_quotation

    confirm_quotation(session, q1.id)
    from sqlalchemy import select

    from app.models import Enrollment
    e1 = session.scalars(select(Enrollment).where(Enrollment.student_id == s1.id)).first()
    contract = ch.create_contract(session, {
        "contract_no": "CT-B-1", "student_id": s1.id, "total_fee": "3820", "currency": "USD",
        "signed_date": "2026-09-01", "refund_rules": [{"stage": "x", "ratio": "0"}],
    })
    ch.create_payment(session, {
        "contract_id": contract.id, "type": "代收代缴-学费", "amount": "3820",
        "currency": "USD", "voucher_no": "V-B-1", "payee": "EV",
    })
    ch.create_document(session, {"student_id": s1.id, "doc_type": "SSP", "doc_no": "SSP-1B"})
    ch.create_document(session, {"student_id": s1.id, "doc_type": "ACR I-Card",
                                 "doc_no": "ACR-B-1", "expiry_date": "2030-01-01"})
    for stage in ("材料准备", "已缴费", "已入学", "在读"):
        from app.services.pipeline import advance_enrollment_stage

        advance_enrollment_stage(session, e1.id, stage)
    from app.services.pipeline import advance_student_stage

    for stu_stage in ("沟通中", "已报名", "在读"):
        advance_student_stage(session, s1.student_no, stu_stage)
    # 学员二：材料准备 + 3 天后入学（临行入学待办）；签证已过期（error 预警）
    s2 = ch.create_student(session, {"student_no": "STU-B-002", "name": "看板学员二（虚构）",
                                     "birth_date": "1999-01-01"})
    ch.create_document(session, {"student_id": s2.id, "doc_type": "护照",
                                 "doc_no": "E2", "expiry_date": "2035-01-01"})
    q2 = create_quotation(session, {
        "student_id": s2.id, "school_id": school.id, "course_id": course.id,
        "weeks": 12, "room_type": "4人间", "start_date": "2026-10-11", "status": "已发送",
    })
    confirm_quotation(session, q2.id)
    e2 = session.scalars(select(Enrollment).where(Enrollment.student_id == s2.id)).first()
    e2.expected_start = date.today() + timedelta(days=3)
    session.flush()
    advance = __import__("app.services.pipeline", fromlist=["advance_enrollment_stage"]).advance_enrollment_stage
    advance(session, e2.id, "材料准备")
    ch.create_document(session, {
        "student_id": s2.id, "doc_type": "签证", "doc_no": "V-EXPIRED",
        "expiry_date": (date.today() - timedelta(days=1)).isoformat(),
    })
    return s1, s2


def test_overview_funnel_and_commission_split(client, session):
    _board_world(session, client)
    data = client.get("/api/compliance/overview").json()
    assert data["funnel"]["student_stages"].get("在读") == 1
    assert data["funnel"]["quote_status"].get("已确认") == 2
    # 两份确认报价佣金 25%×310×12=930/份；学员一已入学 → 应结=930，预估=1860
    assert data["business"]["est_commission_usd"] == "1860"
    assert data["business"]["settleable_commission_usd"] == "930"
    assert data["business"]["in_study"] == 1


def test_overview_expiring_documents(client, session):
    _board_world(session, client)
    docs = client.get("/api/compliance/overview").json()["expiring_documents"]
    ssp = [d for d in docs if d["doc_type"] == "SSP"]
    visa = [d for d in docs if d["doc_type"] == "签证"]
    assert ssp and ssp[0]["level"] == "warning" and ssp[0]["days_left"] == 10
    assert visa and visa[0]["level"] == "error" and visa[0]["days_left"] == -1


def test_overview_follow_ups(client, session):
    _board_world(session, client)
    ups = client.get("/api/compliance/overview").json()["follow_ups"]
    kinds = {u["kind"] for u in ups}
    assert "材料收集中" in kinds
    assert "临行入学" in kinds  # 学员二 3 天后入学
    arrival = next(u for u in ups if u["kind"] == "临行入学")
    assert arrival["urgent"] is True and "3 天后入学" in arrival["detail"]


def test_student_list_summary_columns(client, session):
    _board_world(session, client)
    data = client.get("/api/students/paged").json()
    row1 = next(r for r in data["items"] if r["student_no"] == "STU-B-001")
    assert row1["active_program"] and "在读" in row1["active_program"]
    row2 = next(r for r in data["items"] if r["student_no"] == "STU-B-002")
    assert row2["active_program"] and "材料准备" in row2["active_program"]


def test_contract_list_has_settlement(client, session):
    _board_world(session, client)
    contracts = client.get("/api/contracts").json()
    ct = next(c for c in contracts if c["contract_no"] == "CT-B-1")
    assert ct["settlement"]["receivable_cny"] == "27504.00"
    assert ct["settlement"]["cleared"] is True
    # 学员360聚合同样带对账
    rec = client.get("/api/students/STU-B-001/records").json()
    assert rec["contracts"][0]["settlement"]["paid_cny"] == "27504.00"
