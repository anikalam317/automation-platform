from celery import Celery
from .config import Config

def make_celery(app=None):
    """Create a Celery instance"""
    celery = Celery(
        app.import_name if app else 'laf',
        backend=Config.CELERY_RESULT_BACKEND,
        broker=Config.CELERY_BROKER_URL,
        include=['laf.tasks']
    )
    
    if app:
        # Update celery config with Flask app config
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            """Make celery tasks work with Flask app context."""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

# Create celery instance for worker
celery = make_celery()