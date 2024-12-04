import uuid
from sqlalchemy import Column, DateTime, JSON, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AOI(Base):
    __tablename__ = "aoi"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"),
                     nullable=True)  # Foreign key to the "user" table
    geometry = Column(JSON, nullable=False)  # Geometry stored as JSON
    name = Column(Text, nullable=False)  # Name of the AOI
    description = Column(Text, nullable=True)  # Optional description
    # Automatically set to the current timestamp
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AOI(id={self.id}, user_id={self.user_id}, name={self.name}, created_at={self.created_at})>"
