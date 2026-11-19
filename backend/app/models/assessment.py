import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user = relationship("User", back_populates="assessments")

    input_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    predicted_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    explanation: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )