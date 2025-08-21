#!/usr/bin/env python3
"""
PAT Method Development Workflow Setup Script

This script sets up a complete PAT (Process Analytical Technology) workflow system with:
- Task definitions for PAT method development
- Instrument definitions with status endpoints
- Service definitions and mappings
- Database population with sample data
"""

import json
import os
import sys
from pathlib import Path
import requests
import time

# PAT Workflow Configuration
PAT_TASKS = [
    {
        "name": "Sample Measurement",
        "category": "Preparation",
        "description": "Measure sample weight and properties",
        "required_capabilities": ["balance", "measurement"],
        "optional_capabilities": ["precision_weighing"],
        "estimated_duration_seconds": 300,
        "parameters": {
            "sample_id": {"type": "string", "required": True},
            "target_weight": {"type": "number", "default": 1.0, "unit": "g"},
            "precision": {"type": "number", "default": 0.001, "unit": "g"}
        }
    },
    {
        "name": "Mixing",
        "category": "Operation",
        "description": "Mix materials using automated mixer",
        "required_capabilities": ["mixing", "motor_control"],
        "optional_capabilities": ["temperature_control"],
        "estimated_duration_seconds": 600,
        "parameters": {
            "speed": {"type": "number", "default": 100, "unit": "rpm"},
            "duration": {"type": "number", "default": 300, "unit": "seconds"},
            "temperature": {"type": "number", "default": 25, "unit": "celsius"}
        }
    },
    {
        "name": "Monitor",
        "category": "Data Collection",
        "description": "Monitor process parameters using NIR spectroscopy",
        "required_capabilities": ["spectroscopy", "nir"],
        "optional_capabilities": ["multivariate_analysis"],
        "estimated_duration_seconds": 180,
        "parameters": {
            "wavelength_range": {"type": "string", "default": "1100-2500"},
            "resolution": {"type": "number", "default": 2, "unit": "nm"},
            "scans": {"type": "number", "default": 32}
        }
    },
    {
        "name": "Calibration",
        "category": "Data Analysis",
        "description": "Calibrate analytical models with reference data",
        "required_capabilities": ["data_analysis", "statistical_modeling"],
        "optional_capabilities": ["pls_regression", "cross_validation"],
        "estimated_duration_seconds": 900,
        "parameters": {
            "model_type": {"type": "string", "default": "PLS", "options": ["PLS", "PCR", "MLR"]},
            "validation_method": {"type": "string", "default": "cross_validation"},
            "components": {"type": "number", "default": 5}
        }
    },
    {
        "name": "Code",
        "category": "Calculation",
        "description": "Execute custom calculation and analysis code",
        "required_capabilities": ["computation", "python_execution"],
        "optional_capabilities": ["machine_learning", "data_visualization"],
        "estimated_duration_seconds": 240,
        "parameters": {
            "script_path": {"type": "string", "required": True},
            "input_data": {"type": "object", "default": {}},
            "output_format": {"type": "string", "default": "json"}
        }
    },
    {
        "name": "Blending",
        "category": "Operation",
        "description": "Blend materials using high-shear blender",
        "required_capabilities": ["blending", "high_shear"],
        "optional_capabilities": ["particle_size_control"],
        "estimated_duration_seconds": 450,
        "parameters": {
            "blend_speed": {"type": "number", "default": 1500, "unit": "rpm"},
            "blend_time": {"type": "number", "default": 300, "unit": "seconds"},
            "target_uniformity": {"type": "number", "default": 0.95}
        }
    },
    {
        "name": "Dashboard",
        "category": "Visualization",
        "description": "Display real-time process dashboard",
        "required_capabilities": ["visualization", "web_interface"],
        "optional_capabilities": ["real_time_updates", "alerts"],
        "estimated_duration_seconds": 60,
        "parameters": {
            "update_interval": {"type": "number", "default": 5, "unit": "seconds"},
            "display_metrics": {"type": "array", "default": ["temperature", "pressure", "concentration"]},
            "alert_thresholds": {"type": "object", "default": {}}
        }
    },
    {
        "name": "Control",
        "category": "Control",
        "description": "Automated process control and optimization",
        "required_capabilities": ["process_control", "pid_control"],
        "optional_capabilities": ["adaptive_control", "optimization"],
        "estimated_duration_seconds": 120,
        "parameters": {
            "control_variable": {"type": "string", "required": True},
            "setpoint": {"type": "number", "required": True},
            "pid_parameters": {"type": "object", "default": {"kp": 1.0, "ki": 0.1, "kd": 0.01}}
        }
    }
]

PAT_INSTRUMENTS = [
    {
        "name": "Weight Balance",
        "category": "Equipment",
        "type": "analytical_balance",
        "manufacturer": "Mettler Toledo",
        "model": "XPE205",
        "description": "High-precision analytical balance for sample measurement",
        "endpoint": "http://localhost:5001",
        "status_endpoint": "http://localhost:5001/status",
        "capabilities": ["balance", "measurement", "precision_weighing"],
        "specifications": {
            "max_weight": "220g",
            "readability": "0.01mg",
            "linearity": "0.02mg",
            "interface": "RS232/USB"
        },
        "parameters": {
            "stability_time": 3,
            "auto_tare": True,
            "environmental_monitoring": True
        }
    },
    {
        "name": "Mixer",
        "category": "Equipment", 
        "type": "overhead_stirrer",
        "manufacturer": "IKA",
        "model": "RW20",
        "description": "Overhead stirrer for sample mixing and homogenization",
        "endpoint": "http://localhost:5002",
        "status_endpoint": "http://localhost:5002/status",
        "capabilities": ["mixing", "motor_control", "temperature_control"],
        "specifications": {
            "speed_range": "10-2000 rpm",
            "torque": "50 Ncm",
            "viscosity_max": "10000 mPas",
            "temperature_range": "-10 to 300°C"
        },
        "parameters": {
            "speed_accuracy": "±1%",
            "temperature_accuracy": "±0.5°C",
            "digital_display": True
        }
    },
    {
        "name": "NIR",
        "category": "Sensor",
        "type": "nir_spectrometer", 
        "manufacturer": "Bruker",
        "model": "MPA II",
        "description": "Near-infrared spectrometer for real-time process monitoring",
        "endpoint": "http://localhost:5003",
        "status_endpoint": "http://localhost:5003/status",
        "capabilities": ["spectroscopy", "nir", "multivariate_analysis"],
        "specifications": {
            "wavelength_range": "1000-2500 nm",
            "resolution": "≤2 nm",
            "scan_time": "0.1-10 seconds",
            "detector": "InGaAs"
        },
        "parameters": {
            "integration_time": 100,
            "averaging": 32,
            "reference_measurement": "automatic"
        }
    },
    {
        "name": "Blender",
        "category": "Equipment",
        "type": "high_shear_mixer",
        "manufacturer": "Silverson", 
        "model": "L5M-A",
        "description": "High-shear mixer for blending and particle size reduction",
        "endpoint": "http://localhost:5004",
        "status_endpoint": "http://localhost:5004/status",
        "capabilities": ["blending", "high_shear", "particle_size_control"],
        "specifications": {
            "speed_range": "500-10000 rpm",
            "batch_size": "0.01-20 L",
            "power": "750W",
            "rotor_stator": "standard square hole"
        },
        "parameters": {
            "variable_speed": True,
            "reverse_operation": False,
            "digital_tachometer": True
        }
    },
    {
        "name": "Database",
        "category": "Software",
        "type": "database_server",
        "manufacturer": "PostgreSQL",
        "model": "v14",
        "description": "Database system for data storage and retrieval",
        "endpoint": "http://localhost:5005",
        "status_endpoint": "http://localhost:5005/status", 
        "capabilities": ["data_storage", "sql_queries", "real_time_access"],
        "specifications": {
            "type": "relational_database",
            "concurrent_connections": 100,
            "storage": "unlimited",
            "backup": "continuous"
        },
        "parameters": {
            "connection_pool": 20,
            "query_timeout": 30,
            "auto_vacuum": True
        }
    }
]

PAT_SERVICES = [
    {
        "name": "Run Weight Balance",
        "category": "Sample Measurement",
        "type": "measurement_service",
        "description": "Execute weight measurement using analytical balance",
        "endpoint": "http://localhost:6001",
        "required_instruments": ["Weight Balance"],
        "capabilities": ["balance", "measurement", "data_logging"],
        "parameters": {
            "measurement_mode": "automatic",
            "stabilization_time": 3,
            "number_of_readings": 3,
            "output_format": "json"
        },
        "execution_script": "services/run_weight_balance.py"
    },
    {
        "name": "Run Mixer", 
        "category": "Operation",
        "type": "mixing_service",
        "description": "Execute mixing operation with precise control",
        "endpoint": "http://localhost:6002",
        "required_instruments": ["Mixer"],
        "capabilities": ["mixing", "motor_control", "process_monitoring"],
        "parameters": {
            "mixing_profile": "standard",
            "speed_ramp": True,
            "monitoring_interval": 10,
            "safety_limits": True
        },
        "execution_script": "services/run_mixer.py"
    },
    {
        "name": "Run Blender",
        "category": "Operation", 
        "type": "blending_service",
        "description": "Execute blending operation for material homogenization",
        "endpoint": "http://localhost:6003",
        "required_instruments": ["Blender"],
        "capabilities": ["blending", "high_shear", "quality_control"],
        "parameters": {
            "blend_profile": "high_shear",
            "quality_metrics": ["uniformity", "particle_size"],
            "process_optimization": True
        },
        "execution_script": "services/run_blender.py"
    },
    {
        "name": "Run NIR",
        "category": "Spectroscopy",
        "type": "spectroscopy_service", 
        "description": "Execute NIR spectroscopic analysis with data processing",
        "endpoint": "http://localhost:6004",
        "required_instruments": ["NIR"],
        "capabilities": ["spectroscopy", "nir", "chemometrics"],
        "parameters": {
            "measurement_mode": "reflectance",
            "preprocessing": ["snv", "derivative"],
            "model_application": True,
            "real_time_analysis": True
        },
        "execution_script": "services/run_nir.py"
    },
    {
        "name": "Develop Model",
        "category": "Code",
        "type": "modeling_service",
        "description": "Develop predictive models using multivariate analysis",
        "endpoint": "http://localhost:6005", 
        "required_instruments": ["Database"],
        "capabilities": ["machine_learning", "statistical_modeling", "validation"],
        "parameters": {
            "algorithm": "PLS",
            "validation_method": "cross_validation",
            "feature_selection": True,
            "model_export": "pmml"
        },
        "execution_script": "services/develop_model.py"
    },
    {
        "name": "Apply Model",
        "category": "Code",
        "type": "prediction_service",
        "description": "Apply trained models for real-time prediction",
        "endpoint": "http://localhost:6006",
        "required_instruments": ["Database"],
        "capabilities": ["prediction", "model_inference", "real_time_processing"],
        "parameters": {
            "model_path": "models/",
            "confidence_threshold": 0.8,
            "batch_processing": False,
            "output_logging": True
        },
        "execution_script": "services/apply_model.py"
    },
    {
        "name": "Visualize",
        "category": "Visualization",
        "type": "dashboard_service",
        "description": "Generate real-time visualizations and dashboards",
        "endpoint": "http://localhost:6007",
        "required_instruments": ["Database"],
        "capabilities": ["visualization", "real_time_updates", "interactive_plots"],
        "parameters": {
            "chart_types": ["line", "scatter", "heatmap"],
            "update_frequency": 5,
            "export_formats": ["png", "pdf", "svg"],
            "interactive": True
        },
        "execution_script": "services/visualize.py"
    },
    {
        "name": "Data Extraction",
        "category": "Database",
        "type": "data_service",
        "description": "Extract and process data from multiple sources", 
        "endpoint": "http://localhost:6008",
        "required_instruments": ["Database"],
        "capabilities": ["data_extraction", "etl", "data_transformation"],
        "parameters": {
            "data_sources": ["instruments", "lims", "files"],
            "extraction_schedule": "real_time",
            "data_validation": True,
            "output_format": "json"
        },
        "execution_script": "services/data_extraction.py"
    }
]

def create_instrument_definitions():
    """Create instrument definition files in JSON format"""
    instruments_dir = Path("instrument_definitions")
    instruments_dir.mkdir(exist_ok=True)
    
    # Create instruments.json
    with open(instruments_dir / "instruments.json", "w") as f:
        json.dump(PAT_INSTRUMENTS, f, indent=2)
    
    # Create individual instrument files
    for instrument in PAT_INSTRUMENTS:
        filename = f"{instrument['name'].lower().replace(' ', '_')}.json"
        with open(instruments_dir / filename, "w") as f:
            json.dump(instrument, f, indent=2)
    
    print(f"Created {len(PAT_INSTRUMENTS)} instrument definition files in {instruments_dir}")

def create_task_definitions():
    """Create task definition files in JSON format"""
    tasks_dir = Path("task_definitions")
    tasks_dir.mkdir(exist_ok=True)
    
    # Create tasks.json
    with open(tasks_dir / "tasks.json", "w") as f:
        json.dump(PAT_TASKS, f, indent=2)
    
    # Create individual task files
    for task in PAT_TASKS:
        filename = f"{task['name'].lower().replace(' ', '_')}.json"
        with open(tasks_dir / filename, "w") as f:
            json.dump(task, f, indent=2)
    
    print(f"Created {len(PAT_TASKS)} task definition files in {tasks_dir}")

def create_service_definitions():
    """Create service definition files in JSON format"""
    services_dir = Path("service_definitions")
    services_dir.mkdir(exist_ok=True)
    
    # Create services.json
    with open(services_dir / "services.json", "w") as f:
        json.dump(PAT_SERVICES, f, indent=2)
    
    # Create individual service files
    for service in PAT_SERVICES:
        filename = f"{service['name'].lower().replace(' ', '_')}.json"
        with open(services_dir / filename, "w") as f:
            json.dump(service, f, indent=2)
    
    print(f"Created {len(PAT_SERVICES)} service definition files in {services_dir}")

def create_service_scripts_directory():
    """Create directory structure for service execution scripts"""
    services_dir = Path("services")
    services_dir.mkdir(exist_ok=True)
    
    # Create init file
    with open(services_dir / "__init__.py", "w") as f:
        f.write('"""PAT Method Development Service Scripts"""\n')
    
    print(f"Created services directory structure in {services_dir}")

def create_summary_report():
    """Create a summary report of the PAT workflow setup"""
    report = f"""
# PAT Method Development Workflow Setup Report

## Overview
This setup creates a comprehensive Process Analytical Technology (PAT) workflow system with the following components:

## Tasks ({len(PAT_TASKS)} total)
"""
    
    for task in PAT_TASKS:
        report += f"- **{task['name']}** ({task['category']}): {task['description']}\n"
    
    report += f"\n## Instruments ({len(PAT_INSTRUMENTS)} total)\n"
    
    for instrument in PAT_INSTRUMENTS:
        report += f"- **{instrument['name']}** ({instrument['category']}): {instrument['manufacturer']} {instrument['model']} - {instrument['description']}\n"
    
    report += f"\n## Services ({len(PAT_SERVICES)} total)\n"
    
    for service in PAT_SERVICES:
        report += f"- **{service['name']}** ({service['category']}): {service['description']}\n"
    
    report += """
## Architecture
The system follows a microservices architecture where:

1. **Tasks** define the workflow steps and requirements
2. **Instruments** represent physical/software components with status endpoints
3. **Services** provide executable operations that connect to instruments
4. **Workflows** combine tasks, instruments, and services into executable processes

## Endpoints
- Instrument status endpoints: 5001-5005
- Service execution endpoints: 6001-6008
- All endpoints use HTTP REST API for communication

## Next Steps
1. Implement instrument simulators
2. Create service execution scripts
3. Set up database schemas
4. Update frontend components
5. Test end-to-end workflow execution
"""
    
    with open("PAT_WORKFLOW_SETUP_REPORT.md", "w") as f:
        f.write(report)
    
    print("Created PAT workflow setup report: PAT_WORKFLOW_SETUP_REPORT.md")

def main():
    """Main setup function"""
    print("Setting up PAT Method Development Workflow System...")
    print("=" * 60)
    
    try:
        create_task_definitions()
        create_instrument_definitions() 
        create_service_definitions()
        create_service_scripts_directory()
        create_summary_report()
        
        print("\n" + "=" * 60)
        print("PAT Workflow System Setup Complete!")
        print("\nNext steps:")
        print("1. Run instrument simulators: python -m services.instrument_simulators")
        print("2. Start service endpoints: python -m services.service_runners") 
        print("3. Populate database: python populate_pat_database.py")
        print("4. Test system: python test_pat_workflow.py")
        
    except Exception as e:
        print(f"Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()