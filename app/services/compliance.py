"""活动/项目合规校验（纯函数）。

依据：教基一〔2016〕8号（行前备案30日）、2014境外研学指南（≤2国4城、
小学≤3周/中学≤6周、师生比1:10）、LB/T 091-2025（保险/应急预案）、
旅行社条例（出境游资质）。
"""
from __future__ import annotations

from datetime import date, timedelta

from app.models.agency import Agency
from app.models.program import Program


def agency_to_dict(agency: Agency | None) -> dict | None:
    if agency is None:
        return None
    return {
        "name": agency.name,
        "outbound_licensed": agency.outbound_licensed,
        "license_expiry": agency.license_expiry,
    }


def program_to_dict(program: Program) -> dict:
    return {
        "name": program.name,
        "type": program.type,
        "departure_date": program.departure_date,
        "return_date": program.return_date,
        "filing_date": program.filing_date,
        "filing_status": program.filing_status,
        "status": program.status,
        "dest_country_count": program.dest_country_count,
        "max_cities_per_country": program.max_cities_per_country,
        "student_age_group": program.student_age_group,
        "teacher_count": program.teacher_count,
        "student_count": program.student_count,
        "insurance": program.insurance,
        "emergency_plan": program.emergency_plan,
        "partner_school": program.partner_school,
        "school_verified": program.school_verified,
        "school_id": program.school_id,
        "course_id": program.course_id,
        "weeks": program.weeks,
        "room_type": program.room_type,
    }


def violation(code: str, message: str, level: str = "error") -> dict:
    return {"code": code, "message": message, "level": level}


def check_program(data: dict, agency: dict | None) -> list[dict]:
    """校验单个活动，返回违规列表（level: error/warning）。"""
    out: list[dict] = []
    ptype = data.get("type")
    departure = data.get("departure_date")
    ret = data.get("return_date")
    filing_date = data.get("filing_date")
    filing_status = data.get("filing_status")
    status = data.get("status")

    if agency is None:
        out.append(violation("AGENCY_MISSING", "机构合规档案不存在，无法核验资质"))
        agency = {}

    # ---- 机构资质（通用）----
    expiry = agency.get("license_expiry")
    if isinstance(expiry, date):
        today = date.today()
        if expiry < today:
            out.append(violation("LICENSE_EXPIRED", "旅行社业务经营许可证已过期"))
        elif expiry <= today + timedelta(days=90):
            out.append(violation("LICENSE_EXPIRING", "旅行社业务经营许可证90天内到期", "warning"))

    # ---- 行前备案（境内研学/出境游学通用）----
    if ptype in ("境内研学", "出境游学"):
        if filing_status != "已备案":
            if status == "已成团":
                out.append(violation("NOT_FILED_BUT_TEAM", "未完成行前备案不得成团"))
            else:
                out.append(violation("FILING_PENDING", "活动尚未备案（须行前至少30日备案）", "warning"))
        if filing_date is not None and isinstance(departure, date):
            days = (departure - filing_date).days
            if days < 30:
                out.append(violation("FILING_LESS_THAN_30D", f"行前备案仅{days}天，须至少提前30日"))

    # ---- 出境游学专项 ----
    if ptype == "出境游学":
        if not agency.get("outbound_licensed"):
            out.append(violation("AGENCY_NO_OUTBOUND_LICENSE", "出境游学须持有出境游业务经营许可"))

        if (data.get("dest_country_count") or 0) > 2:
            out.append(violation("TOO_MANY_COUNTRIES", "出境游学行程一般不超过2个国家"))
        if (data.get("max_cities_per_country") or 0) > 4:
            out.append(violation("TOO_MANY_CITIES", "每个国家停留城市不超过4个"))

        if isinstance(departure, date) and isinstance(ret, date):
            days = (ret - departure).days
            limit = 21 if data.get("student_age_group") == "小学" else 42
            if days > limit:
                out.append(violation("DURATION_OVER_LIMIT", f"境外时长{days}天超出上限{limit}天"))

        teachers = data.get("teacher_count") or 0
        students = data.get("student_count") or 0
        if students > 0 and teachers * 10 < students:
            out.append(violation("TEACHER_RATIO", "带队师生比须不低于1:10"))

        insurance = data.get("insurance")
        if not insurance:
            out.append(violation("INSURANCE_REQUIRED", "出境游学须全员投保（含全球救援）"))
        else:
            if not insurance.get("includes_global_rescue"):
                out.append(violation("GLOBAL_RESCUE_REQUIRED", "出境游学保险须提供24小时全球救援"))
            low = []
            if (insurance.get("coverage_per_person_wan") or 0) < 60:
                low.append("每人保额宜高于60万元")
            if (insurance.get("coverage_per_accident_wan") or 0) < 1000:
                low.append("每次事故/每年累计宜高于1000万元")
            if low:
                out.append(violation("INSURANCE_LOW_COVERAGE", "；".join(low), "warning"))

        if not data.get("emergency_plan"):
            out.append(violation("EMERGENCY_PLAN_REQUIRED", "出境游学须制定境外突发事件应急预案"))

        if not data.get("partner_school"):
            out.append(violation("PARTNER_SCHOOL_REQUIRED", "出境游学须登记境外合作学校/机构信息"))
        elif data.get("school_verified") is not True:
            out.append(violation(
                "PARTNER_SCHOOL_NOT_VERIFIED",
                "境外合作学校/机构资质尚未核验（应对照教育涉外监管信息网）", "warning",
            ))

    # ---- 语言研修（个人计划，非研学团）----
    # 不做备案/师生比/应急预案校验；核心是学校库关联与课程价目约束。
    # data["_course"] 由 crud 层按 course_id 注入快照 {min_weeks, room_prices}。
    if ptype == "语言研修":
        if not data.get("school_id"):
            out.append(violation("LANG_SCHOOL_REQUIRED", "语言研修须关联学校库中的合作学校"))
        if not data.get("course_id"):
            out.append(violation("LANG_COURSE_REQUIRED", "语言研修须关联课程价目表中的课程"))
        course = data.get("_course") or {}
        weeks = data.get("weeks") or 0
        room = data.get("room_type")
        if course:
            if weeks and weeks < (course.get("min_weeks") or 0):
                out.append(violation(
                    "WEEKS_BELOW_MIN",
                    f"报名 {weeks} 周低于该课程最短 {course['min_weeks']} 周（保分班等有最短周期要求）",
                ))
            prices = course.get("room_prices") or {}
            if room and room not in prices:
                out.append(violation(
                    "ROOM_TYPE_INVALID",
                    f"房型「{room}」不在该课程价目表内（可选：{'/'.join(prices)}）",
                ))
        if not data.get("insurance"):
            out.append(violation(
                "INSURANCE_SUGGESTED",
                "建议出发前投保含海外医疗的境外游学保险（菲律宾私立医疗费用高）", "warning",
            ))
        return out

    # ---- 境内研学配比提示（1:30，warning）----
    if ptype == "境内研学":
        teachers = data.get("teacher_count") or 0
        students = data.get("student_count") or 0
        if students > 0 and teachers * 30 < students:
            out.append(violation("MENTOR_RATIO", "研学指导人员配比宜不低于1:30", "warning"))

    return out


def has_errors(violations: list[dict]) -> bool:
    return any(v["level"] == "error" for v in violations)
