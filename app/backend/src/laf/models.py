from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
import datetime

db = SQLAlchemy()


class Workflow(db.Model):
    """
    A workflow represents a sequence of tasks that can be executed. For compliance,
    the only columns in a workflow that can be updated are the status and updated_at.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    author = db.Column(db.String(128), nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.now(datetime.timezone.utc)
    )
    tasks = db.relationship(
        "Task", backref="workflow", lazy=True, cascade="all, delete-orphan"
    )
    workflow_hash = db.Column(db.String(64), unique=True)
    status = db.Column(
        db.String(64), default="pending"
    )  # pending, running, completed, failed
    updated_at = db.Column(
        db.DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class Task(db.Model):
    """
    A task represents a unit operation in a workflow. It's action in a
    laboratory process is uniquely defined by a workflow and an order index
    (the sequence in which it is executed). It's actions is defined by a
    recipe, which is a a pre-defined execution service that accepts user
    defined parameters. The only columns in a task that can be updated are
    status.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflow.id"), nullable=False)
    # The order index is used to determine the sequence of tasks in a workflow.
    order_index = db.Column(db.Integer, default=0)
    service = db.relationship("Service", backref="tasks")
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"))
    service_parameters = db.Column(
        JSONB
    )  # Stores parameters and instructions for the service
    service_hash = db.Column(db.String(64), unique=True)  # Hash of service config
    executed_at = db.Column(
        db.DateTime, default=datetime.datetime.now(datetime.timezone.utc)
    )
    status = db.Column(db.String(64), default="pending")
    results = db.relationship(
        "Result", backref="task", lazy=True, cascade="all, delete-orphan"
    )


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.Text)
    type = db.Column(
        db.String(64), nullable=False
    )  # e.g., 'kubernetes', 'http', 'docker'
    endpoint = db.Column(
        db.String(256), nullable=False
    )  # e.g., k8s job name, HTTP URL, etc.
    default_parameters = db.Column(JSONB)  # Optional default params
    enabled = db.Column(db.Boolean, default=True)


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    data = db.Column(JSONB)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.now(datetime.timezone.utc)
    )
