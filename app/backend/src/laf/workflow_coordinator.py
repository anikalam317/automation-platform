import logging
from .models import db, Task

logger = logging.getLogger(__name__)


class WorkflowCoordinator:
    def __init__(self, app):
        self.app = app

    def handle_workflow_change(self, data):
        """Handle workflow status changes"""
        with self.app.app_context():
            workflow_id = data.get("workflow_id")
            operation = data.get("operation", "UPDATE")
            if operation == "INSERT":
                self.start_first_task(workflow_id)
            elif operation == "UPDATE":
                self.process_workflow_update(workflow_id, data)

    def process_workflow_update(self, workflow_id, data):
        """Stub for workflow update logic (extend as needed)."""
        pass

    def handle_task_change(self, data):
        """Handle task status changes"""
        with self.app.app_context():
            task_id = data.get("task_id")
            operation = data.get("operation", "UPDATE")
            if operation == "UPDATE":
                self.process_task_update(task_id, data)

    def get_service(self, task):
        """Fetch the Service for a given task's service mapping"""
        from .models import Service

        service = Service.query.filter_by(id=task.service_id, enabled=True).first()
        if not service:
            logger.error(f"No enabled service found for service_id {task.service_id}")
        return service

    def start_first_task(self, workflow_id):
        """Start the first task in a workflow"""
        try:
            first_task = (
                Task.query.filter_by(workflow_id=workflow_id)
                .order_by(Task.order_index)
                .first()
            )
            if first_task:
                service = self.get_service(first_task)
                if service:
                    from .tasks import launch_service

                    launch_service.delay(
                        first_task.id, service.id, first_task.service_parameters
                    )
        except Exception as e:
            logger.error(f"Error starting first task: {e}")

    def process_task_update(self, task_id, data):
        """Process task status updates and trigger next task if needed"""
        try:
            task = Task.query.get(task_id)
            if not task:
                return
            # If task completed, start next task
            if task.status == "completed":
                self.start_next_task(task)
            elif task.status == "running":
                # Update workflow status to running
                workflow = task.workflow
                if workflow.status == "pending":
                    workflow.status = "running"
                    db.session.commit()
        except Exception as e:
            logger.error(f"Error processing task update: {e}")

    def start_next_task(self, completed_task):
        """Start the next task in the workflow"""
        try:
            next_task = (
                Task.query.filter_by(workflow_id=completed_task.workflow_id)
                .filter(Task.order_index > completed_task.order_index)
                .order_by(Task.order_index)
                .first()
            )
            if next_task:
                from .tasks import launch_service

                service = self.get_service(next_task)
                if service:
                    launch_service.delay(
                        next_task.id, service.id, next_task.service_parameters
                    )
            else:
                # No more tasks, mark workflow as completed
                workflow = completed_task.workflow
                workflow.status = "completed"
                db.session.commit()
        except Exception as e:
            logger.error(f"Error starting next task: {e}")
