"""业务管线：学员生命周期与报名执行阶段的推进规则。

每次推进：校验顺序 → 写服务节点（阶段变更）→ 写审计。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DEMO_ACTOR
from app.models import Contract, Enrollment, Payment, Program, School, ServiceEvent, Student, StudentDocument
from app.services.audit import record_audit
from app.services.errors import ComplianceError, NotFound

STUDENT_STAGES = ["意向", "沟通中", "已报名", "在读", "已毕业"]
STUDENT_LOST = "已流失"  # 特殊：任意阶段可转入
ENROLLMENT_STAGES = ["已报名", "材料准备", "已缴费", "已入学", "在读", "已毕业", "已终止"]
ENROLLMENT_TERMINATED = "已终止"


def _check_forward(current: str, target: str, stages: list[str], special: str) -> None:
    if target == special:
        return  # 流失/终止允许任意阶段转入
    if target not in stages:
        raise ComplianceError(f"STAGE_UNKNOWN: 未知阶段「{target}」")
    cur_idx = stages.index(current) if current in stages else -1
    tgt_idx = stages.index(target)
    if tgt_idx < cur_idx:
        raise ComplianceError(
            f"STAGE_BACKWARD: 阶段只能向前推进（当前「{current}」，不能退回「{target}」）"
        )
    if tgt_idx == cur_idx:
        raise ComplianceError(f"STAGE_SAME: 已处于「{target}」阶段，无需重复推进")


def advance_student_stage(session: Session, student_no: str, target: str,
                          remark: str | None = None, actor: str = DEMO_ACTOR) -> Student:
    student = session.query(Student).filter_by(student_no=student_no).first()
    if student is None:
        raise NotFound("学员不存在")
    _check_forward(student.stage, target, STUDENT_STAGES, STUDENT_LOST)
    old = student.stage
    student.stage = target
    session.flush()
    session.add(ServiceEvent(
        student_id=student.id, event_type="阶段变更", occurred_at=datetime.now(), operator=actor,
        remark=f"学员阶段：{old}→{target}" + (f"（{remark}）" if remark else ""),
    ))
    session.flush()
    record_audit(session, actor, "stage", "student", student.student_no,
                 {"before": old, "after": target, "remark": remark})
    return student


def advance_enrollment_stage(session: Session, enrollment_id: int, target: str,
                             remark: str | None = None, actor: str = DEMO_ACTOR) -> Enrollment:
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment is None:
        raise NotFound("报名不存在")
    _check_forward(enrollment.stage, target, ENROLLMENT_STAGES, ENROLLMENT_TERMINATED)
    program = session.get(Program, enrollment.program_id)

    if target == "已入学":
        paid = session.scalars(
            select(Payment.id)
            .join(Contract, Payment.contract_id == Contract.id)
            .where(Contract.student_id == enrollment.student_id)
            .limit(1)
        ).first()
        if paid is None:
            raise ComplianceError(
                "NEED_PAYMENT: 该学员名下无任何缴费记录，未缴费不得入学（先登记合同与缴费）"
            )

    if target == "在读":
        _check_philippines_chain(session, enrollment, program)

    old = enrollment.stage
    enrollment.stage = target
    session.add(ServiceEvent(
        student_id=enrollment.student_id, event_type="阶段变更", occurred_at=datetime.now(),
        operator=actor,
        remark=f"报名「{program.name if program else enrollment.program_id}」阶段：{old}→{target}"
        + (f"（{remark}）" if remark else ""),
    ))
    session.flush()
    record_audit(session, actor, "stage", "enrollment", str(enrollment.id),
                 {"before": old, "after": target, "remark": remark})
    return enrollment


def _check_philippines_chain(session: Session, enrollment: Enrollment,
                             program: Program | None) -> None:
    """菲律宾行政链（仅语言研修 + 菲律宾学校）：

    - SSP：读 1 周也要办，到校由学校代办，未登记不得进入「在读」；
    - ACR I-Card：课程超过 59 天（约 9 周+）还须办理（随第一次延签）。
    团体营多目的地（新加坡等），SSP 非普适，不做全局拦截。
    """
    if program is None or program.type != "语言研修":
        return
    school = session.get(School, program.school_id) if program.school_id else None
    if school is None or school.country != "菲律宾":
        return

    def _has_doc(doc_type: str) -> bool:
        return session.scalars(
            select(StudentDocument.id)
            .where(
                StudentDocument.student_id == enrollment.student_id,
                StudentDocument.doc_type == doc_type,
            )
            .limit(1)
        ).first() is not None

    if not _has_doc("SSP"):
        raise ComplianceError(
            "SSP_REQUIRED: 菲律宾语言研修须办理 SSP（Special Study Permit，读 1 周也要办），"
            "请在证件材料中登记学员 SSP 后再推进「在读」"
        )
    if (program.weeks or 0) * 7 > 59 and not _has_doc("ACR I-Card"):
        raise ComplianceError(
            "ACR_REQUIRED: 课程超过 59 天（约 9 周以上）须办理 ACR I-Card 外国人登记证"
            "（随第一次延签同步申请），请登记后再推进「在读」"
        )
