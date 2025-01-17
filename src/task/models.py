import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Text, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base
from typing import Union


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


class TaskProcess(Base):

    __tablename__ = "task_processes"

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("task.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    gee_task_id = Column(
        Text,
        primary_key=True,
        nullable=False
    )

    def __repr__(self):
        return f"<TaskProcess(task_id={self.task_id}, gee_task_id={self.gee_task_id})>"


def __init__(self, task_id: Union[uuid.UUID, str], gee_task_id: str):
    if isinstance(task_id, str):
        task_id = uuid.UUID(task_id)
    self.task_id = task_id
    self.gee_task_id = gee_task_id
