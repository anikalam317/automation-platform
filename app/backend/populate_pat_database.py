#!/usr/bin/env python3
"""
Populate database with PAT workflow data
This script populates the database with tasks, instruments, and services for PAT method development
"""

import sys
import os
import json
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app" / "backend" / "src"))

from laf.core.database import SessionLocal, init_db
from laf.models.database import Task, Service, TaskTemplate, Workflow
from laf.models.enhanced_models import ServiceV2, TaskTemplateV2, ServiceCapability, ServiceStatus
from datetime import datetime

def load_pat_definitions():
    """Load PAT definitions from JSON files"""
    
    # Load tasks
    tasks_file = Path("task_definitions/tasks.json")
    if tasks_file.exists():
        with open(tasks_file) as f:
            pat_tasks = json.load(f)
    else:
        print("❌ Task definitions not found. Run setup_pat_workflow.py first.")
        return None, None, None
    
    # Load instruments  
    instruments_file = Path("instrument_definitions/instruments.json")
    if instruments_file.exists():
        with open(instruments_file) as f:
            pat_instruments = json.load(f)
    else:
        print("❌ Instrument definitions not found. Run setup_pat_workflow.py first.")
        return None, None, None
    
    # Load services
    services_file = Path("service_definitions/services.json")
    if services_file.exists():
        with open(services_file) as f:
            pat_services = json.load(f)
    else:
        print("❌ Service definitions not found. Run setup_pat_workflow.py first.")
        return None, None, None
    
    return pat_tasks, pat_instruments, pat_services

def populate_task_templates(db, pat_tasks):
    """Populate task templates (both original and enhanced)"""
    print("📝 Populating task templates...")
    
    for task_data in pat_tasks:
        # Create original TaskTemplate
        task_template = TaskTemplate(
            name=task_data["name"],
            description=task_data["description"],
            category=task_data["category"],
            type="pat_method",
            required_service_type="analytical",
            default_parameters=task_data.get("parameters", {}),
            estimated_duration=task_data.get("estimated_duration_seconds", 300) // 60,
            enabled=True
        )
        
        # Check if already exists
        existing = db.query(TaskTemplate).filter(TaskTemplate.name == task_data["name"]).first()
        if not existing:
            db.add(task_template)
            print(f"  ✅ Added task template: {task_data['name']}")
        else:
            print(f"  ⚠️  Task template already exists: {task_data['name']}")
    
    print("  ℹ️  Enhanced task templates (TaskTemplateV2) skipped until database migration is run")

def populate_services(db, pat_services, pat_instruments):
    """Populate services (original model only for now)"""
    print("🔧 Populating services...")
    
    # Create original services
    for service_data in pat_services:
        service = Service(
            name=service_data["name"],
            description=service_data["description"],
            type=service_data["type"],
            endpoint=service_data["endpoint"],
            default_parameters=service_data.get("parameters", {}),
            enabled=True
        )
        
        # Check if already exists
        existing = db.query(Service).filter(Service.name == service_data["name"]).first()
        if not existing:
            db.add(service)
            print(f"  ✅ Added service: {service_data['name']}")
        else:
            print(f"  ⚠️  Service already exists: {service_data['name']}")
    
    # Also create instrument services using original model
    for instrument_data in pat_instruments:
        service = Service(
            name=f"{instrument_data['name']} Service",
            description=f"Service for {instrument_data['name']} ({instrument_data['model']})",
            type=instrument_data["type"],
            endpoint=instrument_data["endpoint"],
            default_parameters=instrument_data.get("parameters", {}),
            enabled=True
        )
        
        # Check if already exists
        existing = db.query(Service).filter(Service.name == f"{instrument_data['name']} Service").first()
        if not existing:
            db.add(service)
            print(f"  ✅ Added instrument service: {instrument_data['name']} Service")
    
    print(f"  ℹ️  Enhanced services (ServiceV2) skipped until database migration is run")

def create_sample_workflow(db):
    """Create a sample PAT workflow"""
    print("🔄 Creating sample PAT workflow...")
    
    # Check if sample workflow already exists
    existing_workflow = db.query(Workflow).filter(Workflow.name == "PAT Method Development").first()
    if existing_workflow:
        print("  ⚠️  Sample workflow already exists")
        return
    
    # Create workflow
    workflow = Workflow(
        name="PAT Method Development",
        author="System",
        status="pending",
        workflow_hash="pat_method_dev_001",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(workflow)
    db.flush()  # Get the ID
    
    # Get services for task mapping
    services = db.query(Service).all()
    service_map = {s.name: s.id for s in services}
    
    # Create sample tasks
    sample_tasks = [
        {
            "name": "Sample Measurement",
            "order_index": 0,
            "service_name": "Run Weight Balance"
        },
        {
            "name": "Mixing",
            "order_index": 1,
            "service_name": "Run Mixer"
        },
        {
            "name": "Monitor",
            "order_index": 2,
            "service_name": "Run NIR"
        },
        {
            "name": "Calibration",
            "order_index": 3,
            "service_name": "Develop Model"
        }
    ]
    
    for task_data in sample_tasks:
        service_id = service_map.get(task_data["service_name"])
        
        task = Task(
            name=task_data["name"],
            workflow_id=workflow.id,
            order_index=task_data["order_index"],
            service_id=service_id,
            service_parameters={
                "sample_id": "PAT_SAMPLE_001",
                "target_value": 100.0,
                "precision": 0.01
            },
            status="pending",
            executed_at=datetime.now()
        )
        db.add(task)
    
    print(f"  ✅ Created sample workflow with {len(sample_tasks)} tasks")

def main():
    """Main function to populate database"""
    print("PAT Workflow Database Population")
    print("=" * 50)
    
    # Load PAT definitions
    pat_tasks, pat_instruments, pat_services = load_pat_definitions()
    if not all([pat_tasks, pat_instruments, pat_services]):
        print("❌ Failed to load PAT definitions")
        sys.exit(1)
    
    # Initialize database
    print("🗄️  Initializing database...")
    init_db()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Populate data
        populate_task_templates(db, pat_tasks)
        populate_services(db, pat_services, pat_instruments)
        create_sample_workflow(db)
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 50)
        print("✅ Database population completed successfully!")
        print(f"   - {len(pat_tasks)} task templates created")
        print(f"   - {len(pat_services)} services created") 
        print(f"   - {len(pat_instruments)} instrument services created")
        print("   - 1 sample workflow created")
        
        print("\nNext steps:")
        print("1. Start instrument simulators: python start_instrument_simulators.py")
        print("2. Test API endpoints: curl http://localhost:8001/api/tasks/")
        print("3. Access frontend: http://localhost:3000")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    main()