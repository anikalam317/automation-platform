from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading

from ..core.config import settings
from ..core.database import init_db
from .v1 import workflows, tasks, webhooks
try:
    from .v1 import services, ai
except ImportError:
    services = None
    ai = None
from ..services.handlers.notification_listeners import NotificationListener


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()

    # Start notification listener in background thread
    notification_listener = NotificationListener()
    listener_thread = threading.Thread(
        target=notification_listener.start_listener, daemon=True
    )
    listener_thread.start()

    yield
    # Shutdown
    pass


app = FastAPI(
    title="Laboratory Automation Framework",
    description="A framework for managing laboratory workflows and tasks",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflows.router)
app.include_router(tasks.router)
app.include_router(webhooks.router)
if services:
    app.include_router(services.router)
if ai:
    app.include_router(ai.router)
