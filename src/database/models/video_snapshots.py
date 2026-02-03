from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.videos import Videos


class VideoSnapshots(Base):  # noqa: D101
    __tablename__ = "video_snapshots"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    video_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
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

    delta_views_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    delta_likes_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    delta_comments_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    delta_reports_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    video: Mapped["Videos"] = relationship(
        "Videos",
        back_populates="snapshots",
        lazy="select",
    )

    __table_args__ = (
        Index("idx_snapshots_date_video", "created_at", "video_id"),
    )
