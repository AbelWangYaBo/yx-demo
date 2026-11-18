from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Attachment(Base):
    """附件文件登记（内容存 data/attachments/，gitignore）。"""

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))  # 原始文件名
    stored_path: Mapped[str] = mapped_column(Text)  # 相对 data/ 的存储路径
    content_type: Mapped[str] = mapped_column(String(120))
    size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class AccessLog(Base):
    """内部访问记录：查看学员信息/下载资料等敏感读取行为（不进审计哈希链）。

    目的：数据泄露事后追溯。依据《未成年人网络保护条例》第36条
    "记录访问情况"的精神，与审计日志分开存放。
    """

    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(100))
    access_type: Mapped[str] = mapped_column(String(40), index=True)  # VIEW_STUDENT/DOWNLOAD_FILE/...
    target: Mapped[str] = mapped_column(String(120), index=True)  # 学员号 / 附件ID
    detail: Mapped[str | None] = mapped_column(Text)  # JSON 字符串
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
