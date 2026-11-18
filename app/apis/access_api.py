"""内部访问记录路由（查看学员/下载资料的留痕，只读）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_session
from app.services.access import list_access_logs

router = APIRouter(prefix="/api/access-logs", tags=["access-logs"])


@router.get("")
def get_access_logs(student_no: str | None = None,
                    limit: int = Query(default=200, le=500),
                    session: Session = Depends(get_session)):
    logs = list_access_logs(session, student_no=student_no, limit=limit)
    return [
        {
            "id": l.id, "actor": l.actor, "access_type": l.access_type,
            "target": l.target, "detail": l.detail, "created_at": l.created_at,
        }
        for l in logs
    ]
