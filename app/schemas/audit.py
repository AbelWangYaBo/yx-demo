from __future__ import annotations

from pydantic import BaseModel


class AuditOut(BaseModel):
    id: int
    actor: str
    action: str
    entity: str
    entity_id: str
    payload: dict | None
    remark: str | None
    created_at: str
    prev_hash: str
    hash: str


class AuditPage(BaseModel):
    items: list[AuditOut]
    total: int


class VerifyOut(BaseModel):
    valid: bool
    checked: int
    broken_at: int | None
