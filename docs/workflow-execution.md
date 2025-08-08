# Workflow Execution Flow

## Frontend (React)

### 1. Workflow Creation (User Interface)

The user creates a new workflow (TODO: interface to be designed)

_files_
- [App.tsx]('../app/frontend/src/App.tsx')  TODO: Anik to specify the exact file path

### 2. Validation (TODO)

Frontend validates the workflow details using a JSON schema.

_files_
- [worflow.schema.json]('../app/frontend/src/laf/schemas/worflow_schema.json')  TODO: Anik to specify the exact file path

### 3. API Request (HTTPS)

The frontend sends a POST request to the backend with workflow details with
JSON body.

_files_
- [App.tsx]('../app/frontend/src/App.tsx')  TODO: Anik to specify the exact file path

## Backend (FASTAPI)

### 1. Workflow Creation

The backend receives the POST request.

_files_
- [app.py]('../app/backend/src/laf/app.py')

### 2. Validation (Pydantic)

The backed validates the request and workflow details (Pydantic).
TODO: Currently using SQLAlchemy models, need to migrate to Pydantic.

_files_
- [models.py]('../app/backend/src/laf/models.py')

### 3. Workflow Creation

The backend creates a new workflow entry in the database.

_files_
- [app.py]('../app/backend/src/laf/app.py')

## Database (PostgreSQL)

- New entries created in the `workflows` table trigger a database event.
- New entries created in the `tasks` table trigger a database event.
- The backend emits a PostgreSQL NOTIFY event via a database trigger.

_files_
- [database_setup.sql]('../app/backend/src/laf/database_setup.sql')

## Notification Listener (psycopg)

Database listener (using psycopg) listens for the `workflow_changes` event.
starts the workflow.

_files_
- [notification_listener.py]('../app/backend/src/laf/notification_listener.py')

## Backend (continued)

### 4. Workflow Coordinator

- Retrieves task details from the workflow database.
- Updates the workflow status in the database.
- Coordinates task execution.

_files_
- [workflow_coordinator.py]('../app/backend/src/laf/workflow_coordinator.py')

### 5. Task Execution



## Kubernetes Job
- For longer-running tasks, or tasks that benefit from isoloation, such as real
instrument operations, a Kubernetes Job is created.
- This allows for better resource management and isolation, and more modular
workflow building.

---

## 6. Results Update (Backend)

- The backend receives the webhook, updates the task status and results in the
database.
- If there are more tasks in the workflow, the backend schedules the next task via database update, which triggers another notification and service call.

---

## 7. Frontend Update

- The frontend polls or receives updates from the backend (e.g., via polling
`/api/workflows`).
- The UI updates to show the latest task statuses and results, including graphs
and lab visuals.
