"""访问记录（内部）：查看学员信息、下载资料等敏感读取行为留痕。"""
from __future__ import annotations

import json
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import DEMO_ACTOR
from app.models import AccessLog


def _normalize(value):
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def record_access(
    session: Session,
    actor: str,
    access_type: str,
    target: str,
    detail: dict | None = None,
) -> AccessLog:
    log = AccessLog(
        actor=actor or DEMO_ACTOR,
        access_type=access_type,
        target=str(target),
        detail=json.dumps(_normalize(detail or {}), ensure_ascii=False),
    )
    session.add(log)
    session.commit()
    return log


def list_access_logs(session: Session, student_no: str | None = None, limit: int = 200) -> list[AccessLog]:
    logs = (
        session.query(AccessLog)
        .order_by(AccessLog.id.desc())
        .limit(limit)
        .all()
    )
    if student_no:
        logs = [
            l for l in logs
            if l.target == student_no
            or (l.detail and json.loads(l.detail).get("student_no") == student_no)
        ]
    return logs
