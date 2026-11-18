"""附件上传/下载路由。"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import DEMO_ACTOR
from app.db import get_session
from app.services import attachments as att_svc
from app.services.access import record_access

router = APIRouter(tags=["attachments"])


@router.post("/api/attachments", status_code=201)
async def upload_attachment(file: UploadFile, session: Session = Depends(get_session)):
    content = await file.read()
    try:
        att = att_svc.save_attachment(session, file.filename or "file", content, file.content_type or "")
    except HTTPException:
        raise
    return {
        "id": att.id, "filename": att.filename, "size": att.size,
        "content_type": att.content_type,
        "download_url": f"/api/attachments/{att.id}/download",
    }


@router.get("/api/attachments/{attachment_id}/download")
def download_attachment(attachment_id: int, session: Session = Depends(get_session)):
    att = att_svc.get_attachment(session, attachment_id)
    path = att_svc.attachment_file(att)
    record_access(session, DEMO_ACTOR, "DOWNLOAD_FILE", str(att.id), {
        "filename": att.filename, "attachment_id": att.id,
    })
    return FileResponse(path, filename=att.filename, media_type=att.content_type)
