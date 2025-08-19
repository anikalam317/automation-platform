# Laboratory Automation Framework - Integration Guide

## Overview

This integration combines the new React + TypeScript + Material-UI frontend (`app/frontend_new`) with the existing FastAPI backend (`app/backend`) to create a complete Laboratory Automation Framework.

## Architecture Changes

### ✅ **Completed Integration**

1. **TaskTemplate Model Added**: New database model for preconfigured task templates
2. **API Endpoints**: Complete CRUD operations for task templates at `/api/task-templates`
3. **Workflow Controls**: Added pause/stop/resume/delete endpoints for workflows
4. **Frontend Migration**: Moved `Frontend_New` to `app/frontend_new` with proper configuration
5. **Database Migration**: Created migration for TaskTemplate table
6. **Docker Compose**: New `compose_v1.yml` for full LAF setup

### 🏗️ **Project Structure**

```
app/
├── backend/                    # FastAPI backend with PostgreSQL
│   ├── src/laf/
│   │   ├── api/v1/
│   │   │   ├── task_templates.py    # NEW: TaskTemplate CRUD
│   │   │   ├── workflows.py         # UPDATED: Added control endpoints
│   │   │   ├── services.py          # Existing: Service management
│   │   │   └── ai.py               # Existing: AI workflow generation
│   │   ├── models/database.py       # UPDATED: Added TaskTemplate model
│   │   └── schemas/task_template.py # NEW: Pydantic schemas
│   └── migrations/                  # Database migrations
├── frontend_new/               # NEW: React + TS + Material-UI
│   ├── src/
│   │   ├── pages/
│   │   │   ├── TaskManager.tsx     # Task template management
│   │   │   ├── InstrumentManager.tsx # Service management
│   │   │   └── WorkflowBuilder.tsx  # Drag-and-drop workflow builder
│   │   ├── components/
│   │   │   └── NodePalette.tsx     # Unified component palette
│   │   └── services/api.ts         # API client (updated for backend)
│   └── .env                        # VITE_API_URL=http://localhost:8001
└── frontend/                   # Legacy frontend (kept for reference)
```

## Quick Start

### 1. **Database Setup**

```bash
cd app/backend

# Install dependencies
poetry install

# Run migration (when database is available)
poetry run alembic upgrade head

# Seed initial data
poetry run python seed_data.py
```

### 2. **Start with Docker Compose**

```bash
# Use the new compose file
docker-compose -f compose_v1.yml up

# Services will be available at:
# - Backend API: http://localhost:8001
# - Frontend: http://localhost:3000
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### 3. **Development Mode**

**Backend:**
```bash
cd app/backend
poetry run uvicorn laf.api.main:app --reload --port 8001
```

**Frontend:**
```bash
cd app/frontend_new
npm install
npm run dev
```

## API Endpoints

### New TaskTemplate Endpoints
- `GET /api/task-templates` - List all task templates
- `POST /api/task-templates` - Create new task template
- `GET /api/task-templates/{id}` - Get specific task template
- `PUT /api/task-templates/{id}` - Update task template
- `DELETE /api/task-templates/{id}` - Delete task template

### Enhanced Workflow Endpoints
- `POST /api/workflows/{id}/pause` - Pause running workflow
- `POST /api/workflows/{id}/stop` - Stop workflow
- `POST /api/workflows/{id}/resume` - Resume paused workflow
- `DELETE /api/workflows/{id}` - Delete workflow

### Existing Endpoints (Compatible)
- `/api/workflows` - Workflow management
- `/api/services` - Service/instrument management
- `/api/ai/generate-workflow` - AI workflow generation

## Frontend Features

### 🎯 **Clear Architectural Separation**
- **Task Templates**: Reusable workflow steps (e.g., "HPLC Analysis", "Sample Preparation")
- **Services/Instruments**: Physical equipment (e.g., "HPLC System A", "GC-MS System")

### 📊 **Management Pages**
- **Tasks Tab**: Create, edit, delete task templates with categories and parameters
- **Instruments Tab**: Manage laboratory services and equipment
- **Builder Tab**: Drag-and-drop workflow creation with both templates and services
- **Monitor Tab**: Real-time workflow execution monitoring

### 🔄 **Real-time Updates**
- Automatic refresh when adding new templates or services
- Synchronized data across all components
- Event-driven updates on window focus

## Configuration

### Environment Variables

**Backend (.env in app/backend):**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/laf_db
REDIS_URL=redis://localhost:6379
DEBUG=true
```

**Frontend (.env in app/frontend_new):**
```env
VITE_API_URL=http://localhost:8001
NODE_ENV=development
```

## Integration Benefits

### ✅ **Enhanced User Experience**
- Clear separation between task templates and instruments
- Comprehensive CRUD operations for both concepts
- Modern Material-UI interface with proper error handling

### ✅ **Robust Architecture**
- Event-driven backend with PostgreSQL NOTIFY/LISTEN
- TypeScript safety throughout frontend
- Real API integration instead of mock data

### ✅ **Developer Experience**
- Hot module replacement for fast development
- Comprehensive error handling and logging
- Docker compose setup for easy deployment

## Migration from Demo Backend

The integration includes a migration from the previous `demo_backend.py`:

**Before:** In-memory data with simple FastAPI
**After:** PostgreSQL database with event-driven architecture

**Data Migration:**
- Task templates from demo_backend are included in `seed_data.py`
- Services data is preserved and enhanced
- All API contracts remain compatible

## Testing

```bash
# Backend tests
cd app/backend
poetry run pytest

# Frontend tests
cd app/frontend_new
npm run test

# Integration test
curl http://localhost:8001/api/task-templates
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Backend runs on 8001, frontend on 3000
2. **Database connection**: Ensure PostgreSQL is running on 5432
3. **CORS issues**: Backend allows all origins in development
4. **Migration errors**: Run `alembic upgrade head` after database startup

### Logs

```bash
# Backend logs
docker-compose -f compose_v1.yml logs backend

# Frontend logs  
docker-compose -f compose_v1.yml logs frontend_new
```

## Next Steps

1. **Production Setup**: Configure proper CORS, environment variables
2. **Authentication**: Add user authentication system
3. **Real Instruments**: Connect to actual laboratory equipment
4. **Monitoring**: Add application monitoring and metrics
5. **Testing**: Comprehensive integration test suite