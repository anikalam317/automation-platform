from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..core.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    author = Column(String(128), nullable=False)
    status = Column(String(64), default="pending")
    workflow_hash = Column(String(64), unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tasks = relationship(
        "Task", back_populates="workflow", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    order_index = Column(Integer, default=0)
    service_id = Column(Integer, ForeignKey("services.id"))
    service_parameters = Column(JSON)
    service_hash = Column(String(64))
    status = Column(String(64), default="pending")
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    workflow = relationship("Workflow", back_populates="tasks")
    service = relationship("Service", back_populates="tasks")
    results = relationship(
        "Result", back_populates="task", cascade="all, delete-orphan"
    )


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text)
    type = Column(String(64), nullable=False)
    endpoint = Column(String(256), nullable=False)
    default_parameters = Column(JSON)
    enabled = Column(Boolean, default=True)

    tasks = relationship("Task", back_populates="service")


class TaskTemplate(Base):
    __tablename__ = "task_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    category = Column(String(64), nullable=False)  # analytical, preparative, processing, storage
    type = Column(String(64), nullable=False)
    required_service_type = Column(String(64))  # hplc, gc-ms, liquid-handler, etc.
    default_parameters = Column(JSON)
    estimated_duration = Column(Integer, default=30)  # minutes
    enabled = Column(Boolean, default=True)


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    data = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="results")
