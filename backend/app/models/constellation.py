"""Constellation models: tenant-owned resource groups and satellite links."""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Constellation(Base):
    __tablename__ = "constellations"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_constellation_org_slug"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    slug = Column(String(80), nullable=False)
    name = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    is_demo = Column(Boolean, server_default="false", nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization = relationship("Organization", back_populates="constellations")
    satellite_links = relationship(
        "ConstellationSatellite",
        back_populates="constellation",
        cascade="all, delete-orphan",
    )
    planning_requests = relationship("PlanningRequest", back_populates="constellation")


class ConstellationSatellite(Base):
    __tablename__ = "constellation_satellites"

    constellation_id = Column(
        UUID(as_uuid=True), ForeignKey("constellations.id"), primary_key=True
    )
    satellite_id = Column(
        UUID(as_uuid=True), ForeignKey("satellites.id"), primary_key=True
    )
    display_name = Column(String(160), nullable=True)
    enabled = Column(Boolean, server_default="true", nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    constellation = relationship("Constellation", back_populates="satellite_links")
    satellite = relationship("Satellite", back_populates="constellation_links")
