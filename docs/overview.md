# Laboratory Automation Framework (LAF)

## Overview

This repository contains the Laboratory Automation Framework (LAF), a
Python-based framework designed to facilitate the development and execution of
laboratory automation workflows. LAF provides a structured approach to managing
laboratory tasks, integrating with various hardware and software components,
and ensuring reproducibility in scientific experiments.

## Architecture

Web based user interface based on Flask and React. Event-driven architecture
using Celery for task management. PostgreSQL database for storing workflow
definitions, task states, and results. Web hooks are used to trigger workflows
and tasks.



### TODO

**1. Flask-Login + bcrypt (Easiest Start)**
```python
# Simple username/password with proper hashing
# Supports user sessions, login tracking
# Easy audit trail implementation

Flask-Login + Flask-Principal + bcrypt + SQLAlchemy
```

This provides:
- User authentication (Flask-Login)
- Authorization/permissions (Flask-Principal) 
- Secure password storage (bcrypt)
- Audit trail in database (SQLAlchemy)

**2. Websockets instead of Polling**
- Can use the Postgres LISTEN/NOTIFY feature to push updates to the frontend

**3. Data Fabric**
- Need to bring in the Apache services, Kafka, Ranger, NiFi, etc. to handle
data ingestion, processing, and security.


**. 4.
- **Audit trails:** Track all changes, executions, and user actions with timestamps and user IDs.
- **Traceability:** Ensure every workflow, task, and recipe is uniquely identifiable and linked.
- **Reproducibility:** Store all parameters, code references, and versions for every execution.
- **Integrity:** Use hashes to detect changes and ensure definitions are not tampered with.
- **Electronic signatures:** Implement user authentication and authorization for critical actions.
- **Data retention and backup:** Ensure secure, reliable storage and backup of all records.
- **Validation:** Use JSON schemas and Pydantic models to validate all data structures.
- **Access control:** Enforce role-based permissions and restrict access to sensitive operations.

Your current schema and architectural approach support these requirements.  
To reach full FDA compliance (e.g., 21 CFR Part 11), you will need to add electronic signatures, robust access control, and comprehensive audit logging, but your foundation is strong and competitive.

### Workflow Execution Diagram

```mermaid
graph TD
    %% User Actions
    A[Lab Scientist Creates Workflow] --> B[POST /api/workflows]
    
    %% Database Layer
    B --> C[Insert into PostgreSQL Database]
    C --> D[Database Trigger Fires]
    D --> E[PostgreSQL NOTIFY workflow_changes]
    
    %% Webhook Handler Process
    E --> F[WebhookHandler.start_listener<br/>LISTEN workflow_changes]
    F --> G[handle_notification receives event]
    G --> H[handle_workflow_change]
    H --> I[start_first_task]
    
    %% Task Execution
    I --> J[Find First Task in Workflow]
    J --> K[trigger_instrument_service]
    K --> L[Create Kubernetes Job<br/>OR<br/>Call Celery Task]
    
    %% Task Completion Flow
    L --> M[Task Runs on Worker/K8s Pod]
    M --> N[Task Updates Status in Database]
    N --> O[Database Trigger Fires Again]
    O --> P[PostgreSQL NOTIFY task_changes]
    P --> Q[handle_task_change]
    Q --> R{Task Status?}
    
    %% Decision Logic
    R -->|completed| S[start_next_task]
    R -->|running| T[Update Workflow Status]
    R -->|failed| U[Mark Workflow Failed]
    
    %% Next Task or Complete
    S --> V{More Tasks?}
    V -->|Yes| K
    V -->|No| W[Mark Workflow Complete]
    
    %% Real-time Updates
    G --> X[broadcast_to_clients<br/>WebSocket Updates]
    Q --> X
    X --> Y[Frontend Gets Real-time Updates]
    
    %% Styling
    classDef userAction fill:#e1f5fe
    classDef database fill:#f3e5f5
    classDef handler fill:#e8f5e8
    classDef execution fill:#fff3e0
    classDef frontend fill:#fce4ec
    
    class A,B userAction
    class C,D,E,N,O,P database
    class F,G,H,I,Q,S handler
    class J,K,L,M execution
    class X,Y frontend
```

**Key Components Explained:**

1. **User Layer**: Lab scientist creates workflows through the web interface
2. **Database Layer**: PostgreSQL stores data and sends automatic notifications via triggers
3. **Webhook Handler**: Background process that listens for database changes and orchestrates tasks
4. **Task Execution**: Either Kubernetes Jobs (production) or Celery tasks (development)
5. **Real-time Updates**: WebSocket broadcasts keep the frontend synchronized

**Flow Summary:**
- Scientist creates workflow → Database stores it → Trigger sends notification → Handler starts first task → Task runs → Updates database → Next task starts → Repeat until all tasks complete → Frontend shows real-time progress


