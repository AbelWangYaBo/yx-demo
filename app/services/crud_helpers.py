"""CRUD + 合规触发（业务逻辑层）。

所有写函数末尾经 record_audit() 落审计日志；审计先 flush 取主键、
由 record_audit 内部 commit。
"""
from __future__ import annotations

from datetime import date as date_type, datetime, timedelta

from sqlalchemy import Date, DateTime, or_, select
from sqlalchemy.orm import Session

from app.config import DEMO_ACTOR
from app.models import (
    Agency,
    CommunicationLog,
    Consent,
    Contract,
    Course,
    Enrollment,
    Payment,
    Program,
    Quotation,
    School,
    ServiceEvent,
    Staff,
    Student,
    StudentDocument,
    WeeklyReport,
)
from app.services import compliance as cpl
from app.services.audit import record_audit
from app.services.common import is_minor
from app.services.enrollment_rules import check_passport, check_weg
from app.services.errors import ComplianceError, ConsentRequired, NotFound, ProgramViolation


def _cols(model):
    return {c.name for c in model.__table__.columns}


def _clean(model, data: dict) -> dict:
    """按列类型过滤并强制转换：ISO 字符串 → date/datetime（直调时与 API 路径行为一致）。"""
    cols = model.__table__.columns
    out: dict = {}
    for k, v in data.items():
        if k not in cols:
            continue
        if isinstance(v, str):
            col_type = cols[k].type
            if isinstance(col_type, DateTime):
                v = datetime.fromisoformat(v)
            elif isinstance(col_type, Date):
                v = date_type.fromisoformat(v)
        out[k] = v
    return out


def _create(session: Session, model, data: dict, entity: str, actor: str = DEMO_ACTOR,
            audit_payload: dict | None = None):
    clean = _clean(model, data)
    obj = model(**clean)
    session.add(obj)
    session.flush()
    record_audit(session, actor, "create", entity, str(obj.id),
                 audit_payload if audit_payload is not None else clean)
    return obj


# ---------- 机构与人员 ----------

def get_agency(session: Session) -> Agency | None:
    return session.query(Agency).first()


def create_agency(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Agency:
    return _create(session, Agency, data, "agency", actor)


def _update(session: Session, obj, model, data: dict, entity: str, actor: str = DEMO_ACTOR):
    """通用更新：审计 payload 记录变更字段的前值/新值（before/after）。"""
    clean = _clean(model, data)
    before = {k: getattr(obj, k) for k in clean}
    for k, v in clean.items():
        setattr(obj, k, v)
    session.flush()
    record_audit(session, actor, "update", entity, str(obj.id), {"before": before, "after": clean})
    return obj


def update_agency(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Agency:
    agency = get_agency(session)
    if agency is None:
        raise NotFound("机构合规档案不存在")
    return _update(session, agency, Agency, data, "agency", actor)


def create_staff(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Staff:
    return _create(session, Staff, data, "staff", actor)


def update_staff(session: Session, staff_id: int, data: dict, actor: str = DEMO_ACTOR) -> Staff:
    staff = session.get(Staff, staff_id)
    if staff is None:
        raise NotFound("备案人员不存在")
    return _update(session, staff, Staff, data, "staff", actor)


# ---------- 学员主索引 ----------

def create_student(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Student:
    clean = _clean(Student, data)
    obj = Student(**clean)
    session.add(obj)
    session.flush()
    record_audit(session, actor, "create", "student", str(obj.student_no), clean)
    return obj


# ---------- 同意管理 ----------

def create_consent(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Consent:
    return _create(session, Consent, data, "consent", actor)


def revoke_consent(session: Session, consent_id: int, actor: str = DEMO_ACTOR) -> Consent:
    consent = session.get(Consent, consent_id)
    if consent is None:
        raise NotFound("同意记录不存在")
    consent.status = "撤回"
    consent.revoked_at = datetime.now()
    session.flush()
    record_audit(session, actor, "revoke", "consent", str(consent.id), {"status": "撤回"})
    return consent


# ---------- 学校与课程 ----------

def create_school(session: Session, data: dict, actor: str = DEMO_ACTOR) -> School:
    return _create(session, School, data, "school", actor)


def update_school(session: Session, school_id: int, data: dict, actor: str = DEMO_ACTOR) -> School:
    school = session.get(School, school_id)
    if school is None:
        raise NotFound("学校不存在")
    return _update(session, school, School, data, "school", actor)


def create_course(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Course:
    if session.get(School, data.get("school_id")) is None:
        raise NotFound("学校不存在")
    audit_payload = {**data, "school_name": session.get(School, data["school_id"]).name}
    return _create(session, Course, data, "course", actor, audit_payload=audit_payload)


def update_course(session: Session, course_id: int, data: dict, actor: str = DEMO_ACTOR) -> Course:
    course = session.get(Course, course_id)
    if course is None:
        raise NotFound("课程不存在")
    return _update(session, course, Course, data, "course", actor)


# ---------- 活动与备案 ----------

def program_check_data(session: Session, data: dict) -> dict:
    """语言研修按 course_id 注入课程快照（min_weeks/room_prices）供纯函数校验。"""
    merged = dict(data)
    if merged.get("type") == "语言研修" and merged.get("course_id"):
        course = session.get(Course, merged["course_id"])
        if course is not None:
            merged["_course"] = {"min_weeks": course.min_weeks, "room_prices": course.room_prices}
    return merged


def create_program(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Program:
    violations = cpl.check_program(
        program_check_data(session, data), cpl.agency_to_dict(get_agency(session))
    )
    if cpl.has_errors(violations):
        raise ProgramViolation(violations)
    return _create(session, Program, data, "program", actor)


def update_program(session: Session, program_id: int, data: dict, actor: str = DEMO_ACTOR) -> Program:
    program = session.get(Program, program_id)
    if program is None:
        raise NotFound("活动不存在")
    merged = cpl.program_to_dict(program) | _clean(Program, data)
    violations = cpl.check_program(
        program_check_data(session, merged), cpl.agency_to_dict(get_agency(session))
    )
    if cpl.has_errors(violations):
        raise ProgramViolation(violations)
    return _update(session, program, Program, data, "program", actor)


# ---------- 报名（未成年人同意 + 护照 + WEG 校验）----------

def create_enrollment(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Enrollment:
    student = session.get(Student, data.get("student_id"))
    if student is None:
        raise NotFound("学员不存在")

    # 语言研修直建：无现成项目时，事务内先建个人研修计划
    data = dict(data)
    if data.get("program_id") is None and data.get("course_id"):
        data = _create_language_program_for_enrollment(session, data, actor)

    if is_minor(student.birth_date):
        consent = (
            session.query(Consent)
            .filter(
                Consent.student_id == student.id,
                or_(Consent.program_id == data.get("program_id"),
                    Consent.program_id.is_(None)),
                Consent.status == "有效",
                Consent.individual_consent.is_(True),
            )
            .first()
        )
        if consent is None or consent.consent_type != "敏感信息处理":
            raise ConsentRequired(
                f"CONSENT_REQUIRED: 学员 {student.student_no} 为未成年人，"
                "须先取得监护人针对该活动（或机构级通用）的敏感信息处理单独同意（PIPL 第29/31条）"
            )
    program = session.get(Program, data.get("program_id"))
    if program is None:
        raise NotFound("活动不存在")
    passport_error = check_passport(session, student.id, program)
    if passport_error:
        raise ComplianceError(passport_error)
    weg_error = check_weg(session, student, program)
    if weg_error:
        raise ComplianceError(weg_error)
    return _create(session, Enrollment, data, "enrollment", actor)


def _create_language_program_for_enrollment(session: Session, data: dict,
                                            actor: str = DEMO_ACTOR) -> dict:
    """按课程参数生成个人语言研修计划，返回补充了 program_id 与快照的报名数据。"""
    course = session.get(Course, data.get("course_id"))
    if course is None:
        raise NotFound("课程不存在")
    school = session.get(School, course.school_id)
    weeks = data.get("weeks") or 0
    room_type = data.get("room_type") or ""
    start_raw = data.get("start_date")
    start = date_type.fromisoformat(start_raw) if isinstance(start_raw, str) else start_raw
    if start is None:
        raise ComplianceError("LANG_START_REQUIRED: 语言研修报名须提供入学日期（周日入住）")
    program = create_program(session, {
        "name": f"{school.name}·{course.name}（{weeks}周·{room_type}）",
        "type": "语言研修",
        "departure_date": start.isoformat(),
        "return_date": (start + timedelta(days=weeks * 7 - 1)).isoformat(),
        "school_id": school.id, "course_id": course.id,
        "weeks": weeks, "room_type": room_type,
        "status": "进行中",
    }, actor=actor)
    return {
        **data,
        "program_id": program.id,
        "course_name": data.get("course_name") or course.name,
        "accommodation": data.get("accommodation") or room_type,
        "expected_start": data.get("expected_start") or start.isoformat(),
    }


# ---------- 证件材料 / 沟通记录 ----------

def create_document(session: Session, data: dict, actor: str = DEMO_ACTOR) -> StudentDocument:
    student = session.get(Student, data.get("student_id"))
    if student is None:
        raise NotFound("学员不存在")
    audit_payload = {**data, "student_no": student.student_no}
    return _create(session, StudentDocument, data, "document", actor, audit_payload=audit_payload)


def create_communication(session: Session, data: dict, actor: str = DEMO_ACTOR) -> CommunicationLog:
    student = session.get(Student, data.get("student_id"))
    if student is None:
        raise NotFound("学员不存在")
    audit_payload = {**data, "student_no": student.student_no}
    return _create(session, CommunicationLog, data, "communication", actor, audit_payload=audit_payload)


# ---------- 合同 / 缴费 / 服务节点 ----------

def create_contract(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Contract:
    student = session.get(Student, data.get("student_id"))
    if student is None:
        raise NotFound("学员不存在")
    audit_payload = {**data, "student_no": student.student_no}
    return _create(session, Contract, data, "contract", actor, audit_payload=audit_payload)


def create_payment(session: Session, data: dict, actor: str = DEMO_ACTOR) -> Payment:
    if session.get(Contract, data.get("contract_id")) is None:
        raise NotFound("合同不存在")
    return _create(session, Payment, data, "payment", actor)


def create_service_event(session: Session, data: dict, actor: str = DEMO_ACTOR) -> ServiceEvent:
    student = session.get(Student, data.get("student_id"))
    if student is None:
        raise NotFound("学员不存在")
    audit_payload = {**data, "student_no": student.student_no}
    return _create(session, ServiceEvent, data, "service_event", actor, audit_payload=audit_payload)


# ---------- 在读周报 ----------

def create_weekly_report(session: Session, data: dict, actor: str = DEMO_ACTOR) -> WeeklyReport:
    enrollment = session.get(Enrollment, data.get("enrollment_id"))
    if enrollment is None:
        raise NotFound("报名不存在")
    audit_payload = {**data, "student_id": enrollment.student_id}
    return _create(session, WeeklyReport, data, "weekly_report", actor, audit_payload=audit_payload)
