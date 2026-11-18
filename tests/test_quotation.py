"""报价单：明细算价 / 预览 / 确认转报名 / 未成年拦截。"""
import pytest


def _world(session, client):
    from app.services import crud_helpers as ch

    ch.create_agency(session, {"name": "示例远航游学（虚构）", "uscc": "U-QUO", "outbound_licensed": True})
    school = ch.create_school(session, {
        "name": "EV Academy（虚构演示）", "region": "宿务", "style": "斯巴达",
        "commission_rate": "25", "registration_fee_usd": "100",
        "cooperation_agreement": "合作协议（虚构）.pdf", "verified": True,
    })
    course = ch.create_course(session, {
        "school_id": school.id, "name": "IELTS 保分班", "course_type": "IELTS保分",
        "lessons": "1对1×4 + 团体×3", "min_weeks": 12,
        "room_prices": {"4人间": 310, "3人间": 330, "2人间": 365, "1人间": 430},
        "guarantee": "未达 5.5 分免费延长，出勤≥97%",
    })
    student = ch.create_student(session, {
        "student_no": "STU-QUO-001", "name": "报价学员（虚构）", "birth_date": "2000-01-01",
    })
    ch.create_document(session, {
        "student_id": student.id, "doc_type": "护照",
        "doc_no": "E90000001（虚构）", "expiry_date": "2032-01-01",
    })
    return school, course, student


def test_build_quote_items_math(session):
    from app.services.quotation import build_quote_items

    items, total = build_quote_items(
        registration_fee_usd="100", commission_rate="25",
        weekly_price=310, weeks=12, room_type="4人间",
    )
    by_name = {i["name"]: i for i in items}
    assert by_name["学费+食宿（USD 310/周 × 12周 · 4人间）"]["amount"] == "3720"
    assert by_name["学校注册费（一次性，不退）"]["amount"] == "100"
    assert "PHP" in by_name["当地费预估（SSP/延签/水电/教材等，到校披索现付）"]["amount"]
    assert by_name["学校返佣预估（25%，内部）"]["amount"] == "930"
    assert total == "3820"


def test_quote_preview_api(client, session):
    school, course, _ = _world(session, client)
    r = client.post("/api/quotations/preview", json={
        "school_id": school.id, "course_id": course.id, "weeks": 12, "room_type": "2人间",
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total_usd"] == str(365 * 12 + 100)
    assert any("注册费" in i["name"] for i in data["items"])


def test_quote_preview_rejects_weeks_below_min(client, session):
    school, course, _ = _world(session, client)
    r = client.post("/api/quotations/preview", json={
        "school_id": school.id, "course_id": course.id, "weeks": 4, "room_type": "2人间",
    })
    assert r.status_code == 422
    assert "WEEKS_BELOW_MIN" in r.json()["detail"]


def test_quote_create_then_confirm_generates_enrollment(client, session):
    school, course, student = _world(session, client)
    r = client.post("/api/quotations", json={
        "student_id": student.id, "school_id": school.id, "course_id": course.id,
        "weeks": 12, "room_type": "4人间", "start_date": "2027-01-10", "status": "已发送",
    })
    assert r.status_code == 201, r.text
    q = r.json()
    assert q["quote_no"].startswith("QT-")
    assert q["total_usd"] == "3820"

    c = client.post(f"/api/quotations/{q['id']}/confirm")
    assert c.status_code == 200, c.text
    data = client.get(f"/api/students/{student.student_no}/records").json()
    assert len(data["enrollments"]) == 1
    enr = data["enrollments"][0]
    assert enr["program_type"] == "语言研修"
    assert enr["stage"] == "已报名"
    assert enr["quotation_id"] == q["id"]
    assert enr["accommodation"] == "4人间"
    # 确认状态不可重复确认
    c2 = client.post(f"/api/quotations/{q['id']}/confirm")
    assert c2.status_code == 422


def test_quote_confirm_minor_without_consent_blocked(client, session):
    from app.services import crud_helpers as ch

    school, course, _ = _world(session, client)
    minor = ch.create_student(session, {
        "student_no": "STU-QUO-002", "name": "未成年学员（虚构）", "birth_date": "2014-05-01",
        "guardian_name": "家长（虚构）",
    })
    ch.create_document(session, {
        "student_id": minor.id, "doc_type": "护照",
        "doc_no": "E90000002（虚构）", "expiry_date": "2032-01-01",
    })
    r = client.post("/api/quotations", json={
        "student_id": minor.id, "school_id": school.id, "course_id": course.id,
        "weeks": 12, "room_type": "4人间", "start_date": "2027-01-10",
    })
    assert r.status_code == 201
    q = r.json()
    # 语言研修项目尚未生成 → 无有效同意 → 确认被拦截
    c = client.post(f"/api/quotations/{q['id']}/confirm")
    assert c.status_code == 422
    assert "CONSENT_REQUIRED" in c.json()["detail"]
    # 报价单保持未确认
    quotes = client.get(f"/api/students/{minor.student_no}/records").json()["quotations"]
    assert quotes[0]["status"] != "已确认"
