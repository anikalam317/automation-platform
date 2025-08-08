import psycopg2
import psycopg2.extensions
import json
import logging

from .workflow_coordinator import WorkflowCoordinator
from .task_executor import TaskExecutor

logger = logging.getLogger(__name__)


class NotificationListener:
    def __init__(self, app):
        self.app = app
        self.db_config = {
            "host": app.config.get("DB_HOST", "localhost"),
            "port": app.config.get("DB_PORT", 5432),
            "database": app.config.get("DB_NAME", "laf"),
            "user": app.config.get("DB_USER", "postgres"),
            "password": app.config.get("DB_PASSWORD", "password"),
        }
        self.workflow_coordinator = WorkflowCoordinator(app)
        self.task_executor = TaskExecutor(app)

    def start_listener(self):
        """Start listening for PostgreSQL notifications"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("LISTEN workflow_changes;")
            cur.execute("LISTEN task_changes;")
            logger.info("Started PostgreSQL notification listener")
            while True:
                if conn.poll() == psycopg2.extensions.POLL_OK:
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        self.handle_notification(notify.channel, notify.payload)
        except Exception as e:
            logger.error(f"Database listener error: {e}")

    def handle_notification(self, channel, payload):
        """Handle PostgreSQL notifications"""
        try:
            data = json.loads(payload) if payload else {}
            if channel == "workflow_changes":
                self.workflow_coordinator.handle_workflow_change(data)
            elif channel == "task_changes":
                self.workflow_coordinator.handle_task_change(data)
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
