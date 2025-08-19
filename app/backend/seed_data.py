"""
Seed script to populate initial task templates and services.
Run this after database migration to set up demo data.
"""

import asyncio
from sqlalchemy.orm import Session
from src.laf.core.database import get_db, engine
from src.laf.models.database import TaskTemplate, Service

# Initial task templates (from demo_backend.py)
INITIAL_TASK_TEMPLATES = [
    {
        "name": "HPLC Analysis",
        "description": "High Performance Liquid Chromatography analysis",
        "category": "analytical",
        "type": "hplc",
        "required_service_type": "hplc",
        "default_parameters": {
            "column": "C18",
            "flow_rate": "1.0 mL/min",
            "temperature": "30°C",
            "injection_volume": "10µL"
        },
        "estimated_duration": 30,
        "enabled": True
    },
    {
        "name": "Sample Preparation",
        "description": "Automated sample preparation and dilution",
        "category": "preparative",
        "type": "sample-prep",
        "required_service_type": "liquid-handler",
        "default_parameters": {
            "dilution_factor": 10,
            "solvent": "methanol",
            "volume": "1mL"
        },
        "estimated_duration": 15,
        "enabled": True
    },
    {
        "name": "GC-MS Analysis",
        "description": "Gas Chromatography Mass Spectrometry analysis",
        "category": "analytical",
        "type": "gc-ms",
        "required_service_type": "gc-ms",
        "default_parameters": {
            "injection_temp": "250°C",
            "oven_program": "40°C-300°C",
            "scan_range": "50-500 m/z"
        },
        "estimated_duration": 45,
        "enabled": True
    },
    {
        "name": "Data Processing",
        "description": "Automated data analysis and reporting",
        "category": "processing",
        "type": "data-analysis",
        "required_service_type": None,
        "default_parameters": {
            "analysis_type": "quantitative",
            "report_format": "PDF",
            "include_graphs": True
        },
        "estimated_duration": 10,
        "enabled": True
    }
]

# Initial services/instruments (from demo_backend.py)
INITIAL_SERVICES = [
    {
        "name": "HPLC System A",
        "description": "High Performance Liquid Chromatography",
        "type": "hplc",
        "endpoint": "http://localhost:8001/hplc",
        "enabled": True,
        "default_parameters": {
            "column": "C18",
            "flow_rate": "1.0 mL/min",
            "temperature": "30°C"
        }
    },
    {
        "name": "GC-MS System",
        "description": "Gas Chromatography Mass Spectrometry",
        "type": "gc-ms",
        "endpoint": "http://localhost:8002/gcms",
        "enabled": True,
        "default_parameters": {
            "injection_temp": "250°C",
            "oven_program": "custom"
        }
    },
    {
        "name": "Liquid Handler",
        "description": "Automated liquid handling system",
        "type": "liquid-handler",
        "endpoint": "http://localhost:8003/liquidhandler",
        "enabled": True,
        "default_parameters": {
            "tip_type": "1000µL",
            "aspiration_speed": "medium"
        }
    }
]


def seed_database():
    """Populate the database with initial data."""
    
    # Create database session
    db = Session(engine)
    
    try:
        print("Seeding database with initial data...")
        
        # Check if data already exists
        existing_templates = db.query(TaskTemplate).count()
        existing_services = db.query(Service).count()
        
        if existing_templates > 0:
            print(f"Found {existing_templates} existing task templates, skipping task template seeding.")
        else:
            # Seed task templates
            print("Adding initial task templates...")
            for template_data in INITIAL_TASK_TEMPLATES:
                template = TaskTemplate(**template_data)
                db.add(template)
            print(f"Added {len(INITIAL_TASK_TEMPLATES)} task templates")
        
        if existing_services > 0:
            print(f"Found {existing_services} existing services, skipping service seeding.")
        else:
            # Seed services
            print("Adding initial services...")
            for service_data in INITIAL_SERVICES:
                service = Service(**service_data)
                db.add(service)
            print(f"Added {len(INITIAL_SERVICES)} services")
        
        # Commit changes
        db.commit()
        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()