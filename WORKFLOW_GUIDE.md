# Lab Automation Platform - Complete Workflow Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [Workflow Creation](#workflow-creation)
5. [Workflow Execution](#workflow-execution)
6. [Real-time Monitoring](#real-time-monitoring)
7. [API Reference](#api-reference)
8. [Concurrent Workflows](#concurrent-workflows)
9. [Database Access](#database-access)
10. [Troubleshooting](#troubleshooting)
11. [Kubernetes Deployment](#kubernetes-deployment)

---

## System Overview

The Lab Automation Platform is a distributed system designed for pharmaceutical quality control laboratories. It orchestrates complex analytical workflows using containerized lab instruments and provides real-time monitoring and results management.

### Key Features
- **Manual Workflow Execution** - Workflows require explicit execution trigger (Execute button/API)
- **Real-time Monitoring** - Live status updates and progress tracking
- **Concurrent Processing** - Multiple workflows can run simultaneously
- **Distributed Architecture** - Scalable across multiple machines/containers
- **Complete Lab Simulation** - Realistic pharmaceutical analysis workflows
- **Rich Data Capture** - Comprehensive results with chromatographic data
- **Service Auto-Mapping** - Automatic task-to-instrument service mapping
- **Docker Container Orchestration** - Full containerized instrument simulation

---

## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Celery Worker  │
│  (React/TS)     │────│   (FastAPI)     │────│   (Distributed) │
│  Port: 3005     │    │   Port: 8001    │    │  Task Executor  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Redis Message   │
                    │     Broker      │
                    │   Port: 6379    │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Sample Prep     │    │  HPLC System    │    │ PostgreSQL DB   │
│ Station         │    │   Simulator     │    │   (Results)     │
│ Port: 5002      │    │ Port: 5003      │    │ Port: 5432      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack
- **Frontend**: React + TypeScript + Material-UI + Vite
- **Backend**: FastAPI + SQLAlchemy + Pydantic
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL
- **Instrument Simulators**: Flask + Python (Dockerized)
- **Containers**: Docker + Docker Compose
- **Orchestration**: Kubernetes (production)

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.9+ (for local development)
- Node.js 18+ (for frontend development)

### Quick Start

1. **Clone and Start the System**
```bash
# Navigate to project directory
cd automation-platform-FastAPI

# Start all services
docker compose -f compose_v1.yml up -d

# Verify services are running
docker compose -f compose_v1.yml ps
```

2. **Access the System**
- **Frontend**: http://localhost:3005
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

3. **Service Status Check**
```bash
# Check all containers
docker compose -f compose_v1.yml ps

# Expected services:
# - backend (port 8001)
# - frontend_new (port 3005) 
# - worker (Celery)
# - sample-prep-station (port 5002)
# - hplc-system (port 5003)
# - redis (message broker)
# - db (PostgreSQL)
```

---

## Workflow Creation

### Method 1: Frontend Interface (Recommended)

1. **Open the Frontend**
   - Navigate to http://localhost:3005
   - Click on the **"Builder"** tab

2. **Design Your Workflow**
   - Enter workflow name and author
   - Add tasks from available options:
     - **Sample Preparation** - pH adjustment, dilution, filtration
     - **HPLC Analysis System** - Chromatographic purity analysis

3. **Create and Execute Workflow**
   - Click **"Create Workflow"** to save the workflow
   - System automatically maps tasks to instruments with service IDs
   - Click **"Execute"** button to start execution via Celery
   - Monitor progress in real-time

### Method 2: REST API

```bash
# Create a new workflow
curl -X POST http://localhost:8001/api/workflows/ \
-H "Content-Type: application/json" \
-d '{
  "name": "Quality Control Analysis",
  "author": "Lab Technician",
  "tasks": [
    {"name": "Sample Preparation"},
    {"name": "HPLC Analysis System"}
  ]
}'
```

**Response:**
```json
{
  "id": 11,
  "name": "Quality Control Analysis",
  "status": "pending",
  "tasks": [
    {
      "id": 23,
      "name": "Sample Preparation",
      "service_id": 4,
      "status": "pending",
      "service_parameters": {
        "sample_id": "WF11_T1_Quality_Control_Analysis",
        "volume": 10.0,
        "dilution_factor": 2.0,
        "target_ph": 7.0,
        "timeout": 300
      }
    },
    {
      "id": 24, 
      "name": "HPLC Analysis System",
      "service_id": 5,
      "status": "pending",
      "service_parameters": {
        "sample_id": "WF11_T2_Quality_Control_Analysis",
        "method": "USP_assay_method",
        "injection_volume": 10.0,
        "runtime_minutes": 20.0,
        "timeout": 1800
      }
    }
  ]
}
```

### Automatic Task-to-Service Mapping

The system automatically maps task names to lab instruments with dual mapping layers:

#### Database Service Registry:
| Service ID | Service Name | Type | Endpoint | Status |
|------------|--------------|------|----------|--------|
| 1 | Sample Preparation Station | sample_prep | http://sample-prep-station:5002 | ✅ Active |
| 2 | HPLC Analysis System | hplc | http://hplc-system:5003 | ✅ Active |
| 5 | HPLC System A | hplc | http://localhost:8001/hplc | ⚠️ Mock |
| 6 | GC-MS System | gc-ms | http://localhost:8002/gcms | ⚠️ Mock |
| 7 | Liquid Handler | liquid-handler | http://localhost:8003/liquidhandler | ⚠️ Mock |

#### Task Template Registry:
| Template ID | Task Name | Type | Category | Auto-Maps To |
|-------------|-----------|------|----------|---------------|
| 1 | Sample Preparation | sample_prep | preparative | Service ID 1 |
| 2 | HPLC Purity Analysis | hplc_analysis | analytical | Service ID 2 |
| 3 | HPLC Analysis | hplc | analytical | ⚠️ No auto-mapping |
| 4 | GC-MS Analysis | gc-ms | analytical | ⚠️ No auto-mapping |
| 5 | Data Processing | data-analysis | processing | ⚠️ No auto-mapping |

#### Worker Task Mapping (LAB_INSTRUMENT_MAPPING):
| Task Name | Maps To | Endpoint | Action |
|-----------|---------|----------|--------|
| Sample Preparation | ✅ | http://sample-prep-station:5002 | prepare |
| Sample Preparation Station | ✅ | http://sample-prep-station:5002 | prepare |
| HPLC Purity Analysis | ✅ | http://hplc-system:5003 | analyze |
| HPLC Analysis System | ✅ | http://hplc-system:5003 | analyze |
| HPLC Analysis | ✅ | http://hplc-system:5003 | analyze |

---

## Workflow Execution

### Execution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant C as Celery
    participant W as Worker
    participant I as Instruments

    U->>F: Create Workflow
    F->>B: POST /api/workflows/
    B->>B: Map Tasks to Services
    B->>B: Save to Database
    B->>C: Queue Workflow
    C->>W: execute_workflow.delay()
    W->>W: Build Task Chain
    W->>C: Queue Sequential Tasks
    
    loop For Each Task
        C->>W: execute_lab_task.delay()
        W->>I: Reset Instrument
        W->>I: Start Task
        W->>I: Monitor Status
        I-->>W: Progress Updates
        W->>I: Get Results
        W->>B: Update Task Status
    end
    
    W->>B: Mark Workflow Complete
    B-->>F: Status Updates
    F-->>U: Real-time Updates
```

### Execution Phases

#### Phase 1: Workflow Initialization (< 1 second)
- Workflow created in database
- Tasks automatically mapped to services
- Celery worker receives execution request
- Task chain built for sequential execution

#### Phase 2: Task Execution (1-3 minutes per task)
1. **Sample Preparation Task** (~60-90 seconds)
   - Instrument reset and initialization
   - Sample dilution and pH adjustment
   - Filtration and quality check
   - Results: recovery %, actual pH, volume

2. **HPLC Analysis Task** (~90-120 seconds)
   - Column equilibration
   - Sample injection and separation
   - Data acquisition and processing
   - Results: purity %, peak data, chromatogram

#### Phase 3: Completion and Results Storage
- Task results saved to database
- Workflow status updated to "completed"
- Frontend receives real-time updates

### Manual Execution Triggers

```bash
# Trigger specific workflow via Celery
curl -X POST http://localhost:8001/api/workflows/{workflow_id}/execute-celery

# Example response:
{
  "message": "Workflow 11 queued for execution",
  "celery_task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "workflow_name": "Quality Control Analysis"
}
```

---

## Real-time Monitoring

### Method 1: Frontend Dashboard

1. **Navigate to Monitor Tab**
   - Open http://localhost:3005
   - Click **"Monitor"** tab

2. **View Live Status**
   - **Workflow List**: All workflows with current status
   - **Task Progress**: Individual task status and timing
   - **Results Display**: Detailed analytical results

3. **Status Indicators**
   - 🟡 **Pending** - Waiting to start
   - 🔵 **Running** - Currently executing
   - 🟢 **Completed** - Successfully finished
   - 🔴 **Failed** - Error occurred

### Method 2: API Polling

```bash
# Get all workflows
curl -s http://localhost:8001/api/workflows/ | python -m json.tool

# Get specific workflow with tasks
curl -s http://localhost:8001/api/workflows/11 | python -m json.tool

# Monitor specific task
curl -s http://localhost:8001/api/tasks/23 | python -m json.tool
```

### Method 3: Real-time Logs

```bash
# Monitor Celery worker activity
docker compose -f compose_v1.yml logs worker --follow

# Monitor instrument activity
docker compose -f compose_v1.yml logs sample-prep-station --follow
docker compose -f compose_v1.yml logs hplc-system --follow

# Monitor backend API
docker compose -f compose_v1.yml logs backend --follow
```

### Sample Execution Log
```
[15:30:01] Workflow 11 queued for execution via Celery
[15:30:02] Starting workflow execution: Quality Control Analysis (ID: 11)
[15:30:02] Queuing task: Sample Preparation (ID: 23)
[15:30:02] Queuing task: HPLC Analysis System (ID: 24)
[15:30:02] Workflow task chain started with 2 tasks
[15:30:03] Executing lab task: Sample Preparation (ID: 23)
[15:30:04] Task 23 started on instrument, monitoring...
[15:31:12] Task 23 completed successfully
[15:31:13] Executing lab task: HPLC Analysis System (ID: 24)
[15:31:14] Task 24 started on instrument, monitoring...
[15:32:46] Task 24 completed successfully
[15:32:46] Workflow 11 marked as completed
```

---

## API Reference

### Workflow Endpoints

#### Create Workflow
```http
POST /api/workflows/
Content-Type: application/json

{
  "name": "string",
  "author": "string", 
  "tasks": [
    {"name": "Sample Preparation"},
    {"name": "HPLC Analysis System"}
  ]
}
```

#### List Workflows
```http
GET /api/workflows/
```

#### Get Workflow Details
```http
GET /api/workflows/{workflow_id}
```

#### Execute Workflow via Celery
```http
POST /api/workflows/{workflow_id}/execute-celery
```

#### Update Workflow Status
```http
PUT /api/workflows/{workflow_id}
Content-Type: application/json

{
  "status": "running|completed|failed|paused|stopped"
}
```

#### Workflow Control
```http
POST /api/workflows/{workflow_id}/pause
POST /api/workflows/{workflow_id}/resume  
POST /api/workflows/{workflow_id}/stop
```

#### Delete Workflow
```http
DELETE /api/workflows/{workflow_id}
```

### Task Endpoints

#### List Tasks
```http
GET /api/tasks/
```

#### Get Task Details
```http
GET /api/tasks/{task_id}
```

#### Update Task Status
```http
PUT /api/tasks/{task_id}
Content-Type: application/json

{
  "status": "running|completed|failed",
  "results": {...}
}
```

### Concurrent Execution

#### Execute Multiple Workflows
```http
POST /api/workflows/execute-concurrent
Content-Type: application/json

{
  "workflow_ids": [11, 12, 13]
}
```

**Response:**
```json
{
  "message": "Started concurrent execution of 3 workflows",
  "celery_task_id": "group-id-12345",
  "workflow_ids": [11, 12, 13]
}
```

---

## Concurrent Workflows

### Use Cases
- **Parallel Experiments** - Multiple samples analyzed simultaneously
- **Load Testing** - System performance validation
- **Batch Processing** - High-throughput analysis

### Example: Concurrent Execution

```bash
# Create multiple workflows
for i in {1..3}; do
  curl -X POST http://localhost:8001/api/workflows/ \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Batch Sample $i\", \"author\": \"QC Lab\", \"tasks\": [{\"name\": \"Sample Preparation\"}, {\"name\": \"HPLC Analysis System\"}]}"
done

# Execute all concurrently
curl -X POST http://localhost:8001/api/workflows/execute-concurrent \
-H "Content-Type: application/json" \
-d '{"workflow_ids": [12, 13, 14]}'
```

### Monitoring Concurrent Execution

```bash
# Monitor all worker activity
docker compose -f compose_v1.yml logs worker --follow

# Check workflow statuses
curl -s http://localhost:8001/api/workflows/ | python -c "
import sys, json
workflows = json.load(sys.stdin)
for wf in workflows:
    if wf['id'] >= 12:
        print(f'Workflow {wf[\"id\"]}: {wf[\"name\"]} - {wf[\"status\"]}')
"
```

### Scaling Workers

```bash
# Scale Celery workers for higher concurrency
docker compose -f compose_v1.yml up worker --scale worker=3 -d

# Monitor multiple workers
docker compose -f compose_v1.yml logs worker --follow
```

---

## Database Access

### Method 1: API Access (Recommended)
```bash
# Get workflow history
curl -s http://localhost:8001/api/workflows/ | python -m json.tool

# Get detailed results
curl -s http://localhost:8001/api/workflows/11 | python -c "
import sys, json
wf = json.load(sys.stdin)
print(f'Workflow: {wf[\"name\"]} - Status: {wf[\"status\"]}')
for task in wf['tasks']:
    print(f'  {task[\"name\"]}: {task[\"status\"]}')
    if task.get('results'):
        for result in task['results']:
            print(f'    Result: {result[\"data\"]}')
"
```

### Method 2: Direct Database Access
```bash
# Access PostgreSQL database directly via psql
docker compose -f compose_v1.yml exec db psql -U postgres -d lab_automation

# Sample queries:
# \dt  -- List tables
# SELECT * FROM workflows ORDER BY created_at DESC;
# SELECT * FROM tasks WHERE workflow_id = 11;
# SELECT * FROM results WHERE task_id = 23;
```

### Method 3: Database Summary
```bash
# Get complete database summary via API
curl -s http://localhost:8001/api/workflows/ | python -c "
import sys, json
workflows = json.load(sys.stdin)
print(f'Total Workflows: {len(workflows)}')

print('\\nRecent Workflows:')
for wf in workflows[:10]:
    print(f'  [{wf[\"id\"]}] {wf[\"name\"]} - {wf[\"status\"]} ({wf[\"created_at\"]})')
    
    # Count tasks for each workflow
    task_count = len(wf.get('tasks', []))
    print(f'    Tasks: {task_count}')
    
    # Count results
    result_count = sum(len(task.get('results', [])) for task in wf.get('tasks', []))
    print(f'    Results: {result_count}')
"
```

### Export Database
```bash
# Export PostgreSQL database as SQL dump
docker compose -f compose_v1.yml exec db pg_dump -U postgres -d lab_automation > lab_automation_backup.sql

# Export specific workflow data via API
curl -s http://localhost:8001/api/workflows/11 | python -m json.tool > workflow_11_export.json

# Export all workflows
curl -s http://localhost:8001/api/workflows/ | python -m json.tool > all_workflows_export.json
```

---

## Troubleshooting

### Common Issues

#### 1. Workflow Stuck in "Pending" Status
**Problem**: Workflow created but not executing

**Diagnosis**:
```bash
# Check Celery worker status
docker compose -f compose_v1.yml logs worker --tail=10

# Check Redis connection
docker compose -f compose_v1.yml logs redis --tail=5

# Verify task mapping
curl -s http://localhost:8001/api/workflows/{id} | grep service_id
```

**Solutions**:
```bash
# Restart Celery worker
docker compose -f compose_v1.yml restart worker

# Manual execution trigger
curl -X POST http://localhost:8001/api/workflows/{id}/execute-celery

# Check for port conflicts
docker compose -f compose_v1.yml ps
```

#### 2. Instrument Communication Errors
**Problem**: Tasks fail with HTTP errors

**Diagnosis**:
```bash
# Test instrument connectivity
curl -s http://localhost:5002/status  # Sample prep
curl -s http://localhost:5003/status  # HPLC

# Check instrument logs
docker compose -f compose_v1.yml logs sample-prep-station
docker compose -f compose_v1.yml logs hplc-system
```

**Solutions**:
```bash
# Reset instruments
curl -X POST http://localhost:5002/reset
curl -X POST http://localhost:5003/reset

# Restart instrument containers
docker compose -f compose_v1.yml restart sample-prep-station hplc-system
```

#### 3. Database Connection Issues
**Problem**: Cannot save results or workflow status

**Diagnosis**:
```bash
# Check PostgreSQL database status
docker compose -f compose_v1.yml exec db psql -U postgres -c "\l" lab_automation

# Test database connection
docker compose -f compose_v1.yml exec backend python -c "
from app.backend.src.laf.core.database import SessionLocal
try:
    db = SessionLocal()
    print('Database connected successfully')
    db.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

**Solutions**:
```bash
# Restart database and backend
docker compose -f compose_v1.yml restart db backend

# Check database logs
docker compose -f compose_v1.yml logs db --tail=20
```

#### 4. Frontend Not Loading Workflows
**Problem**: Frontend shows empty workflow list

**Diagnosis**:
```bash
# Test backend API
curl -s http://localhost:8001/api/workflows/

# Check CORS settings
curl -H "Origin: http://localhost:3005" http://localhost:8001/api/workflows/

# Check frontend logs
docker compose -f compose_v1.yml logs frontend_new
```

**Solutions**:
```bash
# Restart frontend
docker compose -f compose_v1.yml restart frontend_new

# Clear browser cache and reload
# Check network tab in browser dev tools
```

### Performance Optimization

#### Scale Celery Workers
```bash
# Increase worker concurrency
docker compose -f compose_v1.yml up worker --scale worker=4 -d

# Monitor worker distribution
docker compose -f compose_v1.yml exec worker celery -A laf.tasks.celery_app inspect active
```

#### Redis Monitoring
```bash
# Monitor Redis performance
docker compose -f compose_v1.yml exec redis redis-cli INFO memory
docker compose -f compose_v1.yml exec redis redis-cli INFO stats
```

#### Database Optimization
```bash
# Analyze PostgreSQL database performance
docker compose -f compose_v1.yml exec db psql -U postgres -d lab_automation -c "ANALYZE;"

# Check database size
docker compose -f compose_v1.yml exec db psql -U postgres -d lab_automation -c "SELECT pg_size_pretty(pg_database_size('lab_automation'));"

# Check table sizes
docker compose -f compose_v1.yml exec db psql -U postgres -d lab_automation -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (local or cloud)
- kubectl configured
- Container registry access

### Deployment Architecture

```yaml
# kubernetes-deployment.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: lab-automation

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: lab-automation
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: lab-automation/backend:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          value: "postgresql://user:password@postgres:5432/lab_db"
        - name: CELERY_BROKER_URL
          value: "redis://redis:6379/0"
        - name: SAMPLE_PREP_URL
          value: "http://sample-prep-station:5002"
        - name: HPLC_URL
          value: "http://hplc-system:5003"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: lab-automation
spec:
  replicas: 4
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: worker
        image: lab-automation/backend:latest
        command: ["celery", "-A", "laf.tasks.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
        env:
        - name: DATABASE_URL
          value: "postgresql://user:password@postgres:5432/lab_db"
        - name: CELERY_BROKER_URL
          value: "redis://redis:6379/0"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-prep-station
  namespace: lab-automation
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sample-prep-station
  template:
    metadata:
      labels:
        app: sample-prep-station
    spec:
      containers:
      - name: sample-prep
        image: lab-automation/sample-prep:latest
        ports:
        - containerPort: 5002

---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: lab-automation
spec:
  selector:
    app: backend
  ports:
  - port: 8001
    targetPort: 8001
  type: LoadBalancer

---
apiVersion: v1
kind: Service
metadata:
  name: sample-prep-station
  namespace: lab-automation
spec:
  selector:
    app: sample-prep-station
  ports:
  - port: 5002
    targetPort: 5002
```

### Deployment Steps

1. **Prepare Container Images**
```bash
# Build and tag images
docker build -t lab-automation/backend:latest ./app/backend
docker build -t lab-automation/frontend:latest ./app/frontend_new
docker build -t lab-automation/sample-prep:latest -f- . <<EOF
FROM python:3.9-slim
WORKDIR /app
COPY instruments/sample_prep_station.py /app/
RUN pip install flask requests
EXPOSE 5002
CMD ["python", "sample_prep_station.py"]
EOF

# Push to registry
docker push lab-automation/backend:latest
docker push lab-automation/frontend:latest
docker push lab-automation/sample-prep:latest
```

2. **Deploy to Kubernetes**
```bash
# Apply deployment
kubectl apply -f kubernetes-deployment.yaml

# Check deployment status
kubectl get pods -n lab-automation
kubectl get services -n lab-automation

# Scale workers as needed
kubectl scale deployment celery-worker --replicas=8 -n lab-automation
```

3. **Monitor Deployment**
```bash
# View logs
kubectl logs -f deployment/backend -n lab-automation
kubectl logs -f deployment/celery-worker -n lab-automation

# Monitor resource usage
kubectl top pods -n lab-automation
kubectl top nodes
```

### Production Considerations

#### High Availability
- Multiple replicas for each service
- Pod disruption budgets
- Health checks and readiness probes

#### Security
- Network policies for service isolation
- Secret management for credentials
- RBAC for API access

#### Monitoring
- Prometheus metrics collection
- Grafana dashboards
- AlertManager for notifications

#### Scaling
- Horizontal Pod Autoscaler (HPA)
- Vertical Pod Autoscaler (VPA)
- Cluster autoscaling

### Example Production Configuration

```yaml
# production-values.yaml for Helm
replicaCount:
  backend: 3
  worker: 8
  samplePrep: 4
  hplc: 4

resources:
  backend:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  worker:
    requests:
      memory: "256Mi"  
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

autoscaling:
  enabled: true
  minReplicas: 4
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

monitoring:
  enabled: true
  prometheus: true
  grafana: true
  alerts: true
```

---

## Conclusion

This Lab Automation Platform provides a complete solution for pharmaceutical quality control laboratories with:

✅ **Manual Workflow Execution** - Workflows require explicit execution trigger (Execute button/API)
✅ **Real-time Monitoring** - Live status updates and progress tracking  
✅ **Concurrent Processing** - Multiple workflows running simultaneously  
✅ **Distributed Architecture** - Scalable across containers and clusters  
✅ **Complete Results Management** - Rich analytical data capture  
✅ **Production Ready** - Kubernetes deployment and monitoring  

The system is designed for both laboratory efficiency and IT infrastructure scalability, making it suitable for organizations from small labs to large pharmaceutical companies.

For support or additional features, please refer to the API documentation at http://localhost:8001/docs or contact the development team.