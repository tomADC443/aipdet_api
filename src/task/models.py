import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Text, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base


class Task(Base):
    __tablename__ = "task"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"),
                     nullable=False)
    aoi_id = Column(UUID(as_uuid=True), ForeignKey("aoi.id"),
                    nullable=False)
    name = Column(Text, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    status = Column(Text, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<AOI(id={self.id}, user_id={self.user_id}, name={self.name}, created_at={self.created_at})>"
