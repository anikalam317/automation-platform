from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading

from ..core.config import settings
from ..core.database import init_db
from .v1 import workflows, tasks, webhooks
try:
    from .v1 import services, ai, task_templates, instrument_management
except ImportError:
    services = None
    ai = None
    task_templates = None
    instrument_management = None
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
    description="""
## Lab Automation Platform API

A comprehensive platform for pharmaceutical quality control laboratories featuring:

- **Manual Workflow Execution** - Workflows require explicit execution trigger (Execute button/API)
- **Real-time Monitoring** - Live status updates and progress tracking via WebSocket and polling
- **Concurrent Processing** - Multiple workflows can run simultaneously using Celery task queue
- **Distributed Architecture** - Scalable across Docker containers and Kubernetes clusters
- **Complete Lab Simulation** - Realistic HPLC analysis and sample preparation workflows
- **Rich Data Capture** - Comprehensive results with chromatographic data and quality metrics
- **Service Auto-Mapping** - Automatic task-to-instrument service mapping with fallback parameters
- **Docker Orchestration** - Full containerized instrument simulation and coordination

### Execution Model
1. Create workflows via frontend builder or API
2. System automatically maps tasks to available lab instruments
3. Manually trigger execution using `/execute-celery` endpoint or frontend Execute button
4. Monitor progress in real-time via status polling or WebSocket connections
5. Access detailed results and analytical data through results API

### Key Endpoints
- `POST /api/workflows/` - Create new workflow with automatic service mapping
- `POST /api/workflows/{id}/execute-celery` - **Manual execution trigger** (required)
- `GET /api/workflows/` - List all workflows with status and task information
- `POST /api/workflows/execute-concurrent` - Execute multiple workflows simultaneously
- `GET /api/workflows/{id}` - Get detailed workflow status, tasks, and results
- `POST /api/workflows/{id}/pause|stop|resume` - Workflow control operations

### Architecture
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Task Queue**: Celery + Redis for distributed execution
- **Instruments**: Flask-based simulators (Sample Prep Station, HPLC System)
- **Frontend**: React + TypeScript + Material-UI + Vite
    """,
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
if task_templates:
    app.include_router(task_templates.router)
if instrument_management:
    app.include_router(instrument_management.router)
