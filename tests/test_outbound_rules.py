"""出境游学增强规则：境外合作学校、护照有效期校验。"""
from datetime import date

from app.services.compliance import check_program


def _base(**ov):
    data = {
        "name": "出境冬令营（虚构）", "type": "出境游学",
        "departure_date": date(2027, 1, 20), "return_date": date(2027, 2, 2),
        "filing_date": date(2026, 12, 1), "filing_status": "已备案", "status": "筹备中",
        "dest_country_count": 1, "max_cities_per_country": 2,
        "student_age_group": "中学", "teacher_count": 2, "student_count": 16,
        "insurance": {"policy_no": "INS-001", "coverage_per_person_wan": 80,
                      "coverage_per_accident_wan": 1200, "includes_global_rescue": True},
        "emergency_plan": True,
        "partner_school": "新加坡某某学校（虚构）", "school_verified": True,
    }
    data.update(ov)
    return data


AGENCY = {"name": "示例游学服务有限公司", "outbound_licensed": True, "license_expiry": date(2028, 12, 31)}


def test_partner_school_required():
    v = check_program(_base(partner_school=None), AGENCY)
    codes = {x["code"] for x in v}
    assert "PARTNER_SCHOOL_REQUIRED" in codes
    assert any(x["code"] == "PARTNER_SCHOOL_REQUIRED" and x["level"] == "error" for x in v)


def test_partner_school_unverified_is_warning():
    v = check_program(_base(school_verified=False), AGENCY)
    assert any(x["code"] == "PARTNER_SCHOOL_NOT_VERIFIED" and x["level"] == "warning" for x in v)


def test_school_fields_not_required_for_domestic():
    v = check_program(_base(type="境内研学", partner_school=None, school_verified=False), AGENCY)
    codes = {x["code"] for x in v}
    assert "PARTNER_SCHOOL_REQUIRED" not in codes
    assert "PARTNER_SCHOOL_NOT_VERIFIED" not in codes
