from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import BigInteger, DateTime, Index, func, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.video_snapshots import VideoSnapshots


class Videos(Base):  # noqa: D101
    __tablename__ = "videos"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    creator_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    video_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    views_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    likes_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    comments_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    reports_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    snapshots: Mapped[list["VideoSnapshots"]] = relationship(
        "VideoSnapshots",
        back_populates="video",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        Index("idx_videos_creator_date", "creator_id", "video_created_at"),
        Index("idx_videos_date_views", "video_created_at", "views_count"),
    )
