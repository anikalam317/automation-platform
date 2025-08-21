#!/usr/bin/env python3
"""
Run database migration to create enhanced service architecture
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "sqlite:///test.db"  # Use the same database as the application

def run_migration():
    """Run the enhanced service architecture migration"""
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("Starting enhanced service architecture migration...")
        
        # Read and execute the migration script
        migration_file = os.path.join(
            os.path.dirname(__file__), 
            "migrations", "versions", "002_enhanced_service_architecture.py"
        )
        
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        # Read the SQL commands from the migration file
        # For SQLite, we'll create the tables directly using SQLAlchemy
        
        # Create enhanced service tables
        migration_sql = """
        -- Services table
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            type VARCHAR(100) NOT NULL,
            category VARCHAR(100) NOT NULL,
            endpoint VARCHAR(500) NOT NULL,
            health_check_endpoint VARCHAR(500),
            status VARCHAR(50) NOT NULL DEFAULT 'offline',
            current_load INTEGER NOT NULL DEFAULT 0,
            max_concurrent_tasks INTEGER NOT NULL DEFAULT 1,
            priority INTEGER NOT NULL DEFAULT 5,
            location VARCHAR(255),
            capabilities TEXT,  -- JSON as TEXT for SQLite
            configuration TEXT, -- JSON as TEXT for SQLite
            metadata TEXT,      -- JSON as TEXT for SQLite
            cost_per_hour DECIMAL(10,2),
            last_heartbeat TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Task templates table
        CREATE TABLE IF NOT EXISTS task_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            category VARCHAR(100) NOT NULL,
            required_capabilities TEXT,  -- JSON array as TEXT
            optional_capabilities TEXT,  -- JSON array as TEXT
            default_parameters TEXT,     -- JSON as TEXT
            parameter_schema TEXT,       -- JSON schema as TEXT
            estimated_duration_seconds INTEGER NOT NULL DEFAULT 3600,
            resource_requirements TEXT,  -- JSON as TEXT
            tags TEXT,                   -- JSON array as TEXT
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Service capabilities table
        CREATE TABLE IF NOT EXISTS service_capabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER NOT NULL,
            capability_name VARCHAR(255) NOT NULL,
            capability_value TEXT,  -- JSON as TEXT
            confidence_score DECIMAL(3,2) NOT NULL DEFAULT 1.0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
        );

        -- User service preferences table
        CREATE TABLE IF NOT EXISTS user_service_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(255) NOT NULL,
            task_type VARCHAR(255),
            preferred_service_ids TEXT,      -- JSON array as TEXT
            blacklisted_service_ids TEXT,    -- JSON array as TEXT
            priority_weight DECIMAL(3,2) NOT NULL DEFAULT 0.5,
            cost_weight DECIMAL(3,2) NOT NULL DEFAULT 0.3,
            speed_weight DECIMAL(3,2) NOT NULL DEFAULT 0.7,
            reliability_weight DECIMAL(3,2) NOT NULL DEFAULT 0.8,
            max_wait_time_seconds INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Workflow execution queue table
        CREATE TABLE IF NOT EXISTS workflow_execution_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            preferred_service_ids TEXT,    -- JSON array as TEXT
            assigned_service_id INTEGER,
            priority INTEGER NOT NULL DEFAULT 5,
            estimated_start_time TIMESTAMP,
            estimated_completion_time TIMESTAMP,
            actual_start_time TIMESTAMP,
            actual_completion_time TIMESTAMP,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            queue_position INTEGER,
            retry_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_service_id) REFERENCES services(id)
        );

        -- Service performance metrics table
        CREATE TABLE IF NOT EXISTS service_performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER NOT NULL,
            task_type VARCHAR(255),
            average_duration_seconds DECIMAL(10,2),
            success_rate DECIMAL(5,4),
            uptime_percentage DECIMAL(5,2),
            error_count INTEGER NOT NULL DEFAULT 0,
            total_executions INTEGER NOT NULL DEFAULT 0,
            recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
        );

        -- Task dependencies table
        CREATE TABLE IF NOT EXISTS task_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            dependent_task_id INTEGER NOT NULL,
            prerequisite_task_id INTEGER NOT NULL,
            dependency_type VARCHAR(50) NOT NULL DEFAULT 'finish_to_start',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
            FOREIGN KEY (dependent_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (prerequisite_task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );

        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_services_status ON services(status);
        CREATE INDEX IF NOT EXISTS idx_services_type ON services(type);
        CREATE INDEX IF NOT EXISTS idx_queue_status ON workflow_execution_queue(status);
        CREATE INDEX IF NOT EXISTS idx_queue_workflow ON workflow_execution_queue(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_queue_service ON workflow_execution_queue(assigned_service_id);
        CREATE INDEX IF NOT EXISTS idx_performance_service ON service_performance_metrics(service_id);
        """
        
        # Check existing services table structure and add missing columns
        alter_services_sql = """
        -- Add missing columns to services table
        ALTER TABLE services ADD COLUMN status VARCHAR(50) DEFAULT 'offline';
        ALTER TABLE services ADD COLUMN current_load INTEGER DEFAULT 0;
        ALTER TABLE services ADD COLUMN max_concurrent_tasks INTEGER DEFAULT 1;
        ALTER TABLE services ADD COLUMN priority INTEGER DEFAULT 5;
        ALTER TABLE services ADD COLUMN location VARCHAR(255);
        ALTER TABLE services ADD COLUMN category VARCHAR(100) DEFAULT 'general';
        ALTER TABLE services ADD COLUMN health_check_endpoint VARCHAR(500);
        ALTER TABLE services ADD COLUMN capabilities TEXT;  -- JSON as TEXT for SQLite
        ALTER TABLE services ADD COLUMN configuration TEXT; -- JSON as TEXT for SQLite
        ALTER TABLE services ADD COLUMN service_metadata TEXT; -- JSON as TEXT for SQLite
        ALTER TABLE services ADD COLUMN cost_per_hour DECIMAL(10,2);
        ALTER TABLE services ADD COLUMN last_heartbeat TIMESTAMP;
        ALTER TABLE services ADD COLUMN created_at TIMESTAMP;
        ALTER TABLE services ADD COLUMN updated_at TIMESTAMP;
        """
        
        # Execute each ALTER TABLE statement individually and catch errors
        for statement in alter_services_sql.split(';'):
            statement = statement.strip()
            if statement and statement.startswith('ALTER'):
                try:
                    session.execute(text(statement))
                    logger.info(f"Executed: {statement[:50]}...")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info(f"Column already exists, skipping: {statement[:50]}...")
                    else:
                        logger.warning(f"Failed to execute: {statement[:50]}... - {str(e)}")
        
        # Create enhanced task templates table if it doesn't exist with the right structure
        enhanced_task_templates_sql = """
        CREATE TABLE IF NOT EXISTS enhanced_task_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            category VARCHAR(100) NOT NULL,
            required_capabilities TEXT,  -- JSON array as TEXT
            optional_capabilities TEXT,  -- JSON array as TEXT
            default_parameters TEXT,     -- JSON as TEXT
            parameter_schema TEXT,       -- JSON schema as TEXT
            estimated_duration_seconds INTEGER NOT NULL DEFAULT 3600,
            resource_requirements TEXT,  -- JSON as TEXT
            tags TEXT,                   -- JSON array as TEXT
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        session.execute(text(enhanced_task_templates_sql))
        
        session.commit()
        logger.info("Enhanced service architecture migration completed successfully!")
        
        # Create sample services for testing
        create_sample_services(session)
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        session.rollback()
        session.close()
        return False

def create_sample_services(session):
    """Create sample services for testing"""
    try:
        logger.info("Creating sample services...")
        
        # First, update existing services with enhanced fields
        session.execute(text("""
            UPDATE services 
            SET 
                status = 'online',
                current_load = 0,
                max_concurrent_tasks = 1,
                priority = 5,
                category = 'analytical',
                capabilities = '{"sample_prep": true, "hplc": true}',
                cost_per_hour = 100.0
            WHERE id = 1
        """))
        
        session.execute(text("""
            UPDATE services 
            SET 
                status = 'online',
                current_load = 0,
                max_concurrent_tasks = 1,
                priority = 5,
                category = 'analytical',
                capabilities = '{"sample_prep": true, "hplc": true}',
                cost_per_hour = 100.0
            WHERE id = 2
        """))
        
        # Check if our enhanced services exist
        sample_prep = session.execute(
            text("SELECT id FROM services WHERE name = 'Sample Preparation Station'")
        ).fetchone()
        
        hplc_system = session.execute(
            text("SELECT id FROM services WHERE name = 'HPLC System Enhanced'")
        ).fetchone()
        
        # Create enhanced services if they don't exist
        if not sample_prep:
            session.execute(text("""
                INSERT INTO services (
                    name, type, category, endpoint, description, enabled, 
                    status, current_load, max_concurrent_tasks, priority, 
                    capabilities, cost_per_hour, health_check_endpoint
                ) VALUES (
                    'Sample Preparation Station', 'sample_prep', 'preparative', 
                    'http://localhost:5002', 'Enhanced sample preparation station', 1,
                    'online', 0, 2, 3,
                    '{"balance": true, "pipette": true, "heating": true, "cooling": true, "ph_measurement": true}',
                    50.0, 'http://localhost:5002/status'
                )
            """))
            logger.info("Created Sample Preparation Station")
        
        if not hplc_system:
            session.execute(text("""
                INSERT INTO services (
                    name, type, category, endpoint, description, enabled,
                    status, current_load, max_concurrent_tasks, priority,
                    capabilities, cost_per_hour, health_check_endpoint
                ) VALUES (
                    'HPLC System Enhanced', 'hplc', 'analytical',
                    'http://localhost:5003', 'Enhanced HPLC analytical system', 1,
                    'online', 0, 1, 2,
                    '{"hplc": true, "uv_detector": true, "autosampler": true, "column_oven": true, "data_processing": true}',
                    150.0, 'http://localhost:5003/status'
                )
            """))
            logger.info("Created HPLC System Enhanced")
        
        session.commit()
        logger.info("Sample services updated/created successfully!")
        
    except Exception as e:
        logger.error(f"Failed to create sample services: {str(e)}")
        session.rollback()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)