"""审计日志：追加写 + SHA-256 哈希链。

- 所有写操作经 record_audit() 落日志，hash 覆盖 prev_hash + 业务字段 + payload + 时间戳
- 不提供任何修改/删除日志的接口；verify_chain() 可检测链上任一篡改
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def _normalize(value):
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def canonical_payload(payload: dict | None) -> str:
    return json.dumps(_normalize(payload or {}), ensure_ascii=False, sort_keys=True)


def compute_log_hash(
    prev_hash: str,
    actor: str,
    action: str,
    entity: str,
    entity_id: str,
    payload_json: str,
    created_at: str,
) -> str:
    raw = "|".join([prev_hash or "", actor, action, entity, entity_id or "", payload_json, created_at])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def record_audit(
    session: Session,
    actor: str,
    action: str,
    entity: str,
    entity_id: str,
    payload: dict | None = None,
    remark: str | None = None,
) -> AuditLog:
    payload_json = canonical_payload(payload)
    created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="microseconds")
    prev = session.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(1)).scalar_one_or_none()
    log = AuditLog(
        actor=actor,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        payload=_normalize(payload or {}),
        remark=remark,
        created_at=created_at,
        prev_hash=prev.hash if prev else "",
        hash=compute_log_hash(
            prev.hash if prev else "", actor, action, entity, str(entity_id), payload_json, created_at
        ),
    )
    session.add(log)
    session.commit()
    return log


def verify_chain(session: Session) -> dict:
    logs = session.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    prev_hash = ""
    for log in logs:
        expected = compute_log_hash(
            prev_hash,
            log.actor,
            log.action,
            log.entity,
            log.entity_id,
            canonical_payload(log.payload),
            log.created_at,
        )
        if log.prev_hash != prev_hash or log.hash != expected:
            return {"valid": False, "checked": logs.index(log), "broken_at": log.id}
        prev_hash = log.hash
    return {"valid": True, "checked": len(logs), "broken_at": None}
