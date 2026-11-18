from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import AuditLog
from app.schemas import AuditPage, VerifyOut
from app.services.audit import verify_chain

router = APIRouter(tags=["audit"])


@router.get("/api/audit", response_model=AuditPage)
def list_audit(
    offset: int = 0,
    limit: int = Query(default=100, le=500),
    session: Session = Depends(get_session),
):
    total = session.scalar(select(func.count()).select_from(AuditLog)) or 0
    items = session.scalars(select(AuditLog).order_by(AuditLog.id.desc()).offset(offset).limit(limit)).all()
    return {"items": items, "total": total}


@router.get("/api/audit/verify", response_model=VerifyOut)
def audit_verify(session: Session = Depends(get_session)):
    return verify_chain(session)


@router.api_route("/api/audit/{log_id}", methods=["PUT", "PATCH", "DELETE"])
def audit_write_forbidden(log_id: int):
    """审计日志追加写：明确拒绝任何修改/删除（无 Allow 语义，直接 405）。"""
    from fastapi import HTTPException

    raise HTTPException(405, "审计日志为追加写，禁止修改/删除")
