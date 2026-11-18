"""合规业务规则测试（纯函数，输入为 dict）。

规则依据见 docs/design.md 第5节与 research/03 报告。
"""
from datetime import date

from app.services.compliance import check_program


def _base_program(**overrides):
    data = {
        "name": "示例冬令营",
        "type": "出境游学",
        "departure_date": date(2027, 1, 20),
        "return_date": date(2027, 2, 2),
        "filing_date": date(2026, 12, 1),
        "filing_status": "已备案",
        "status": "筹备中",
        "dest_country_count": 1,
        "max_cities_per_country": 3,
        "student_age_group": "中学",
        "teacher_count": 2,
        "student_count": 16,
        "insurance": {
            "policy_no": "INS-001",
            "coverage_per_person_wan": 80,
            "coverage_per_accident_wan": 1200,
            "includes_global_rescue": True,
        },
        "emergency_plan": True,
        "partner_school": "境外合作学校（虚构）",
        "school_verified": True,
    }
    data.update(overrides)
    return data


def _licensed_agency(**overrides):
    agency = {
        "name": "示例游学服务有限公司",
        "outbound_licensed": True,
        "license_expiry": date(2028, 12, 31),
    }
    agency.update(overrides)
    return agency


def test_outbound_without_license_is_error():
    violations = check_program(_base_program(), _licensed_agency(outbound_licensed=False))
    codes = {v["code"] for v in violations}
    assert "AGENCY_NO_OUTBOUND_LICENSE" in codes
    assert all(v["level"] == "error" for v in violations if v["code"] == "AGENCY_NO_OUTBOUND_LICENSE")


def test_filing_less_than_30_days_before_departure_is_error():
    # 出发 2027-01-20，备案 2027-01-05 → 仅 15 天
    violations = check_program(_base_program(filing_date=date(2027, 1, 5)), _licensed_agency())
    codes = {v["code"] for v in violations}
    assert "FILING_LESS_THAN_30D" in codes


def test_filing_30_days_is_ok():
    # 出发 2027-01-20，备案 2026-12-21 → 恰好 30 天
    violations = check_program(_base_program(filing_date=date(2026, 12, 21)), _licensed_agency())
    assert "FILING_LESS_THAN_30D" not in {v["code"] for v in violations}


def test_became_team_without_filing_is_error():
    violations = check_program(
        _base_program(filing_status="未备案", filing_date=None, status="已成团"),
        _licensed_agency(),
    )
    assert "NOT_FILED_BUT_TEAM" in {v["code"] for v in violations}


def test_destination_limits_two_countries_four_cities():
    violations = check_program(
        _base_program(dest_country_count=3, max_cities_per_country=5),
        _licensed_agency(),
    )
    codes = {v["code"] for v in violations}
    assert "TOO_MANY_COUNTRIES" in codes
    assert "TOO_MANY_CITIES" in codes


def test_duration_limit_primary_vs_middle():
    # 小学 ≤21 天：26 天超限
    v1 = check_program(
        _base_program(student_age_group="小学", departure_date=date(2027, 1, 20), return_date=date(2027, 2, 14)),
        _licensed_agency(),
    )
    assert "DURATION_OVER_LIMIT" in {x["code"] for x in v1}
    # 中学 ≤42 天：同样 26 天不超
    v2 = check_program(
        _base_program(student_age_group="中学", departure_date=date(2027, 1, 20), return_date=date(2027, 2, 14)),
        _licensed_agency(),
    )
    assert "DURATION_OVER_LIMIT" not in {x["code"] for x in v2}


def test_teacher_ratio_1_to_10_for_outbound():
    violations = check_program(_base_program(teacher_count=1, student_count=16), _licensed_agency())
    assert "TEACHER_RATIO" in {v["code"] for v in violations}


def test_outbound_insurance_required():
    violations = check_program(_base_program(insurance=None), _licensed_agency())
    assert "INSURANCE_REQUIRED" in {v["code"] for v in violations}
    # 有保单但无全球救援
    v2 = check_program(
        _base_program(insurance={"policy_no": "INS-002", "coverage_per_person_wan": 60,
                                 "coverage_per_accident_wan": 1000, "includes_global_rescue": False}),
        _licensed_agency(),
    )
    assert "GLOBAL_RESCUE_REQUIRED" in {v["code"] for v in v2}


def test_low_insurance_coverage_is_warning_not_error():
    violations = check_program(
        _base_program(insurance={"policy_no": "INS-003", "coverage_per_person_wan": 50,
                                 "coverage_per_accident_wan": 800, "includes_global_rescue": True}),
        _licensed_agency(),
    )
    low = [v for v in violations if v["code"] == "INSURANCE_LOW_COVERAGE"]
    assert low and all(v["level"] == "warning" for v in low)


def test_emergency_plan_required_for_outbound():
    violations = check_program(_base_program(emergency_plan=False), _licensed_agency())
    assert "EMERGENCY_PLAN_REQUIRED" in {v["code"] for v in violations}


def test_license_expiring_soon_is_warning_expired_is_error():
    soon = date.today().replace(year=date.today().year)  # 90 天内
    from datetime import timedelta
    soon = date.today() + timedelta(days=30)
    v = check_program(_base_program(), _licensed_agency(license_expiry=soon))
    assert any(v_["code"] == "LICENSE_EXPIRING" and v_["level"] == "warning" for v_ in v)
    expired = date.today() - timedelta(days=1)
    v2 = check_program(_base_program(), _licensed_agency(license_expiry=expired))
    assert any(x["code"] == "LICENSE_EXPIRED" and x["level"] == "error" for x in v2)


def test_domestic_program_skips_outbound_rules():
    data = _base_program(type="境内研学", insurance=None, emergency_plan=False,
                         dest_country_count=None, max_cities_per_country=None)
    violations = check_program(data, _licensed_agency(outbound_licensed=False))
    codes = {v["code"] for v in violations}
    assert "INSURANCE_REQUIRED" not in codes
    assert "AGENCY_NO_OUTBOUND_LICENSE" not in codes
    assert "EMERGENCY_PLAN_REQUIRED" not in codes


def test_clean_program_has_no_errors():
    violations = check_program(_base_program(), _licensed_agency())
    assert [v for v in violations if v["level"] == "error"] == []
