"""学员列表分页搜索 + 查看（含访问记录）。"""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import DEMO_ACTOR
from app.models import CommunicationLog, Enrollment, Program, Student
from app.services.access import record_access
from app.services.aggregation import collect_student_records
from app.services.errors import StudentNotFound


def search_students(session: Session, keyword: str | None = None,
                    page: int = 1, size: int = 20) -> dict:
    stmt = select(Student)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Student.name.like(like), Student.student_no.like(like)))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    students = session.scalars(
        stmt.order_by(Student.student_no).offset((page - 1) * size).limit(size)
    ).all()
    items = [_row_with_summary(session, s) for s in students]
    return {"items": items, "total": total, "page": page, "size": size}


def _row_with_summary(session: Session, student: Student) -> dict:
    """列表行 = 学员基础字段 + 顾问视角摘要（最近沟通 / 在跟项目）。"""
    last_comm = session.scalar(
        select(func.max(CommunicationLog.occurred_at))
        .where(CommunicationLog.student_id == student.id)
    )
    active = session.execute(
        select(Enrollment, Program)
        .join(Program, Enrollment.program_id == Program.id)
        .where(Enrollment.student_id == student.id)
        .order_by(Enrollment.id.desc())
        .limit(1)
    ).first()
    return {
        "id": student.id,
        "student_no": student.student_no,
        "name": student.name,
        "birth_date": student.birth_date.isoformat(),
        "stage": student.stage,
        "guardian_name": student.guardian_name,
        "guardian_phone": student.guardian_phone,
        "last_communication_at": last_comm.isoformat() if last_comm else None,
        "active_program": (
            f"{active[1].name}（{active[0].stage}）" if active else None
        ),
    }


def view_student(session: Session, student_no: str, actor: str = DEMO_ACTOR) -> dict:
    """查看学员基本信息（写访问记录）。"""
    student = session.scalars(
        select(Student).where(Student.student_no == student_no)
    ).first()
    if student is None:
        raise StudentNotFound(f"学员不存在: {student_no}")
    record_access(session, actor, "VIEW_STUDENT", student_no, {
        "student_no": student_no, "name": student.name,
    })
    return {
        "id": student.id, "student_no": student.student_no, "name": student.name,
        "birth_date": student.birth_date.isoformat() if student.birth_date else None,
        "stage": student.stage,
        "guardian_name": student.guardian_name, "guardian_phone": student.guardian_phone,
        "guardian_id_masked": student.guardian_id_masked, "notes": student.notes,
    }


def view_student_records(session: Session, student_no: str, actor: str = DEMO_ACTOR) -> dict:
    """查看学员全量记录：归集 + 写内部访问记录（不进审计链）。"""
    data = collect_student_records(session, student_no)  # 未找到会抛 StudentNotFound
    record_access(session, actor, "VIEW_STUDENT", student_no, {
        "student_no": student_no, "name": data["student"]["name"],
    })
    return data
