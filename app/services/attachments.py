"""附件存储：保存到 data/attachments/YYYY-MM/（分片，gitignore）。"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import DEMO_ACTOR
from app.db import DATA_DIR
from app.models import Attachment
from app.services.audit import record_audit
from app.services.errors import NotFound

MAX_SIZE = 10 * 1024 * 1024  # 10MB
ATTACHMENT_DIR = DATA_DIR / "attachments"


def _safe_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "_", name or "file")
    return name[:180]


def save_attachment(session: Session, filename: str, content: bytes,
                    content_type: str = "application/octet-stream",
                    actor: str = DEMO_ACTOR) -> Attachment:
    if len(content) > MAX_SIZE:
        from fastapi import HTTPException

        raise HTTPException(413, "附件超过 10MB 上限")

    subdir = datetime.now().strftime("%Y-%m")
    target_dir = ATTACHMENT_DIR / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    stored = target_dir / f"{ts}_{_safe_filename(filename)}"
    stored.write_bytes(content)

    att = Attachment(
        filename=filename or stored.name,
        stored_path=str(stored.relative_to(DATA_DIR)),
        content_type=content_type or "application/octet-stream",
        size=len(content),
    )
    session.add(att)
    session.flush()
    record_audit(session, actor, "create", "attachment", str(att.id), {
        "filename": att.filename, "size": att.size, "content_type": att.content_type,
    })
    return att


def get_attachment(session: Session, attachment_id: int) -> Attachment:
    att = session.get(Attachment, attachment_id)
    if att is None:
        raise NotFound("附件不存在")
    return att


def attachment_file(att: Attachment) -> Path:
    return DATA_DIR / att.stored_path
