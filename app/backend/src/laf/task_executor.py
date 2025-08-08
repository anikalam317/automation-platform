import logging
from .models import db

logger = logging.getLogger(__name__)


class TaskExecutor:
    def __init__(self, app):
        self.app = app

    def trigger_service(self, task):
        """Trigger the service for a task"""
        try:
            from .tasks import launch_service

            service = self.get_service(task)
            if service:
                launch_service.delay(task.id, service.id, task.service_parameters)
                logger.info(
                    f"Triggered Celery task for service {service.name} and task {task.id}"
                )
                # Update task status to running
                task.status = "running"
                db.session.commit()
            else:
                logger.error(f"No service found for task {task.id}")
        except Exception as e:
            logger.error(f"Error triggering service: {e}")
            # Mark task as failed
            task.status = "failed"
            db.session.commit()
