from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.database import Base


class PackCapture(Base):
    __tablename__ = "pack_captures"

    id = Column(UUID(as_uuid=True), primary_key=True)
    org_id = Column(String, nullable=False)
    order_id = Column(String, nullable=False)
    image_key = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="captured")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(UUID(as_uuid=True), primary_key=True)
    org_id = Column(String, nullable=False)
    capture_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pack_captures.id"),
        nullable=False,
    )
    verdict = Column(String, nullable=False)
    result = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())