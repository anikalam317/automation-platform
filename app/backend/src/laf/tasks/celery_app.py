from celery import Celery

from ..core.config import settings

celery_app = Celery(
    "laf",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["laf.tasks.workers", "laf.tasks.plugin_workers"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
