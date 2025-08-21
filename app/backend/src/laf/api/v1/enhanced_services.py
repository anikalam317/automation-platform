"""
Enhanced ServiceV2 Management API - Dynamic service registry and discovery endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from ...core.database import get_db
from ...models.enhanced_models import ServiceV2, ServiceStatus, ServiceCapability, ServicePerformanceMetric
from ...core.service_registry import ServiceV2Registry, ServiceV2Config, LoadBalancingStrategy
from ...core.capability_matcher import CapabilityMatcher, TaskRequirements
from ...schemas.enhanced_schemas import (
    ServiceV2Response, ServiceV2Create, ServiceV2Update, ServiceV2HealthResponse,
    ServiceV2DiscoveryRequest, ServiceV2DiscoveryResponse, LoadMetricsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/services", tags=["Enhanced ServiceV2s"])

@router.get("/", response_model=List[ServiceV2Response])
async def list_services(
    status: Optional[ServiceV2Status] = Query(None, description="Filter by service status"),
    category: Optional[str] = Query(None, description="Filter by service category"),
    capability: Optional[str] = Query(None, description="Filter by capability"),
    available_only: bool = Query(False, description="Show only available services"),
    db: Session = Depends(get_db)
):
    """
    List all registered services with optional filtering
    
    **Filters:**
    - **status**: online, offline, busy, maintenance, error
    - **category**: analytical, preparative, storage, etc.
    - **capability**: specific capability name
    - **available_only**: only services accepting new tasks
    """
    try:
        query = db.query(ServiceV2)
        
        # Apply filters
        if status:
            query = query.filter(ServiceV2.status == status)
        if category:
            query = query.filter(ServiceV2.category == category)
        if capability:
            query = query.filter(ServiceV2.capabilities.op('?')(capability))
        if available_only:
            query = query.filter(
                ServiceV2.status == ServiceV2Status.ONLINE,
                ServiceV2.current_load < ServiceV2.max_concurrent_tasks
            )
        
        services = query.all()
        
        logger.info(f"Retrieved {len(services)} services with filters: status={status}, category={category}")
        return services
        
    except Exception as e:
        logger.error(f"Failed to list services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve services: {str(e)}")

@router.post("/", response_model=ServiceV2Response)
async def register_service(
    service_data: ServiceV2Create,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new service in the system
    
    **ServiceV2 Registration Process:**
    1. Validates service configuration
    2. Creates service record with capabilities
    3. Performs initial health check
    4. Starts background monitoring
    
    **Required Fields:**
    - **name**: Unique service name
    - **type**: ServiceV2 type (hplc, sample_prep, balance, etc.)
    - **endpoint**: ServiceV2 HTTP endpoint URL
    - **capabilities**: Dict of service capabilities
    """
    try:
        service_registry = ServiceV2Registry(db)
        
        # Create service configuration
        config = ServiceV2Config(
            name=service_data.name,
            type=service_data.type,
            category=service_data.category,
            endpoint=service_data.endpoint,
            health_check_endpoint=service_data.health_check_endpoint,
            capabilities=service_data.capabilities,
            max_concurrent_tasks=service_data.max_concurrent_tasks,
            priority=service_data.priority,
            location=service_data.location,
            configuration=service_data.configuration,
            service_metadata=service_data.service_metadata,
            cost_per_hour=service_data.cost_per_hour
        )
        
        # Register service
        service = await service_registry.register_service(config)
        
        # Schedule background health monitoring
        background_tasks.add_task(_start_service_monitoring, service.id, db)
        
        logger.info(f"Successfully registered service: {service.name} (ID: {service.id})")
        return service
        
    except Exception as e:
        logger.error(f"Failed to register service: {str(e)}")
        raise HTTPException(status_code=400, detail=f"ServiceV2 registration failed: {str(e)}")

@router.get("/{service_id}", response_model=ServiceV2Response)
async def get_service(service_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific service"""
    service = db.query(ServiceV2).filter(ServiceV2.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="ServiceV2 not found")
    return service

@router.put("/{service_id}", response_model=ServiceV2Response)
async def update_service(
    service_id: int,
    service_update: ServiceV2Update,
    db: Session = Depends(get_db)
):
    """Update service configuration"""
    try:
        service = db.query(ServiceV2).filter(ServiceV2.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="ServiceV2 not found")
        
        # Update fields
        update_data = service_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(service, field, value)
        
        service.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Updated service {service_id}: {list(update_data.keys())}")
        return service
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update service {service_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"ServiceV2 update failed: {str(e)}")

@router.delete("/{service_id}")
async def unregister_service(service_id: int, db: Session = Depends(get_db)):
    """Unregister a service from the system"""
    try:
        service = db.query(ServiceV2).filter(ServiceV2.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="ServiceV2 not found")
        
        # Check if service has pending tasks
        from ...models.enhanced_models import WorkflowExecutionQueue, QueueStatus
        pending_tasks = db.query(WorkflowExecutionQueue).filter(
            WorkflowExecutionQueue.assigned_service_id == service_id,
            WorkflowExecutionQueue.status.in_([QueueStatus.PENDING, QueueStatus.RUNNING])
        ).count()
        
        if pending_tasks > 0:
            raise HTTPException(
                status_code=409, 
                detail=f"Cannot unregister service with {pending_tasks} pending/running tasks"
            )
        
        db.delete(service)
        db.commit()
        
        logger.info(f"Unregistered service {service_id}: {service.name}")
        return {"message": f"ServiceV2 {service.name} unregistered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to unregister service {service_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ServiceV2 unregistration failed: {str(e)}")

@router.get("/{service_id}/health", response_model=ServiceV2HealthResponse)
async def check_service_health(service_id: int, db: Session = Depends(get_db)):
    """Check real-time health status of a specific service"""
    try:
        service = db.query(ServiceV2).filter(ServiceV2.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="ServiceV2 not found")
        
        service_registry = ServiceV2Registry(db)
        health_status = await service_registry._health_check_service(service)
        
        return ServiceV2HealthResponse(
            service_id=service.id,
            service_name=service.name,
            status=health_status.status,
            last_heartbeat=health_status.last_heartbeat,
            response_time_ms=health_status.response_time_ms,
            error_message=health_status.error_message,
            current_load=service.current_load,
            max_concurrent_tasks=service.max_concurrent_tasks,
            load_percentage=service.get_load_percentage()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed for service {service_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/{service_id}/metrics", response_model=LoadMetricsResponse)
async def get_service_metrics(service_id: int, db: Session = Depends(get_db)):
    """Get comprehensive performance metrics for a service"""
    try:
        service_registry = ServiceV2Registry(db)
        metrics = await service_registry.get_service_metrics(service_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="ServiceV2 metrics not found")
        
        return LoadMetricsResponse(
            service_id=metrics.service_id,
            current_load=metrics.current_load,
            max_concurrent_tasks=metrics.max_concurrent_tasks,
            load_percentage=metrics.load_percentage,
            average_response_time=metrics.average_response_time,
            success_rate=metrics.success_rate,
            uptime_percentage=metrics.uptime_percentage,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for service {service_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@router.post("/discover", response_model=ServiceV2DiscoveryResponse)
async def discover_services_for_task(
    discovery_request: ServiceV2DiscoveryRequest,
    db: Session = Depends(get_db)
):
    """
    Discover services capable of handling specific task requirements
    
    **Discovery Process:**
    1. Analyzes task requirements and capabilities
    2. Finds services with matching capabilities
    3. Scores services based on capability match quality
    4. Applies user preferences and constraints
    5. Returns ranked list of suitable services
    
    **Request Parameters:**
    - **required_capabilities**: Must-have capabilities
    - **optional_capabilities**: Nice-to-have capabilities  
    - **constraints**: Additional filters (cost, location, etc.)
    - **user_preferences**: User-specific preferences
    """
    try:
        service_registry = ServiceV2Registry(db)
        capability_matcher = CapabilityMatcher(db)
        
        # Build task requirements
        requirements = TaskRequirements(
            task_type=discovery_request.task_type,
            required_capabilities=discovery_request.required_capabilities,
            optional_capabilities=discovery_request.optional_capabilities or [],
            resource_requirements=discovery_request.resource_requirements or {},
            performance_requirements=discovery_request.performance_requirements or {},
            constraints=discovery_request.constraints or {}
        )
        
        # Discover matching services
        available_services = await service_registry.discover_services(
            requirements.required_capabilities,
            requirements.optional_capabilities,
            requirements.constraints
        )
        
        if not available_services:
            return ServiceV2DiscoveryResponse(
                task_type=discovery_request.task_type,
                discovered_services=[],
                total_matches=0,
                discovery_time=datetime.utcnow(),
                recommendations=["No services found matching requirements"]
            )
        
        # Score services based on capability match
        match_scores = capability_matcher.match_capabilities(requirements, available_services)
        
        # Convert to response format
        discovered_services = []
        for score in match_scores[:10]:  # Top 10 matches
            service = next(s for s in available_services if s.id == score.service_id)
            discovered_services.append({
                "service_id": service.id,
                "service_name": service.name,
                "service_type": service.type,
                "category": service.category,
                "endpoint": service.endpoint,
                "status": service.status,
                "current_load": service.current_load,
                "max_concurrent_tasks": service.max_concurrent_tasks,
                "match_quality": score.quality.value,
                "match_score": score.score,
                "required_match_rate": score.required_match_rate,
                "optional_match_rate": score.optional_match_rate,
                "confidence": score.confidence,
                "reasons": score.reasons,
                "cost_per_hour": service.cost_per_hour
            })
        
        # Generate recommendations
        recommendations = []
        if len(match_scores) < 3:
            recommendations.append("Consider registering additional services for better redundancy")
        
        poor_matches = [s for s in match_scores if s.quality.value in ['poor', 'incompatible']]
        if poor_matches:
            recommendations.append(f"{len(poor_matches)} services have poor capability matches")
        
        return ServiceV2DiscoveryResponse(
            task_type=discovery_request.task_type,
            discovered_services=discovered_services,
            total_matches=len(match_scores),
            discovery_time=datetime.utcnow(),
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"ServiceV2 discovery failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ServiceV2 discovery failed: {str(e)}")

@router.post("/health-check-all")
async def health_check_all_services(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger health check for all registered services"""
    try:
        service_registry = ServiceV2Registry(db)
        
        # Perform health checks in background
        background_tasks.add_task(_perform_health_checks, db)
        
        service_count = db.query(ServiceV2).count()
        
        return {
            "message": f"Health check initiated for {service_count} services",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate health checks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check initiation failed: {str(e)}")

@router.post("/{service_id}/load")
async def update_service_load(
    service_id: int,
    load_change: int,
    db: Session = Depends(get_db)
):
    """Update service current load (internal API)"""
    try:
        service_registry = ServiceV2Registry(db)
        await service_registry.update_service_load(service_id, load_change)
        
        service = db.query(ServiceV2).filter(ServiceV2.id == service_id).first()
        
        return {
            "service_id": service_id,
            "new_load": service.current_load if service else None,
            "updated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to update service load: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Load update failed: {str(e)}")

@router.get("/{service_id}/capabilities")
async def get_service_capabilities(service_id: int, db: Session = Depends(get_db)):
    """Get detailed capabilities for a service"""
    try:
        service = db.query(ServiceV2).filter(ServiceV2.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="ServiceV2 not found")
        
        capabilities = db.query(ServiceV2Capability).filter(
            ServiceV2Capability.service_id == service_id
        ).all()
        
        capability_details = []
        for cap in capabilities:
            capability_details.append({
                "name": cap.capability_name,
                "value": cap.capability_value,
                "confidence_score": float(cap.confidence_score),
                "created_at": cap.created_at
            })
        
        return {
            "service_id": service_id,
            "service_name": service.name,
            "capabilities": service.capabilities,
            "detailed_capabilities": capability_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get capabilities for service {service_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Capability retrieval failed: {str(e)}")

# Background task functions

async def _start_service_monitoring(service_id: int, db: Session):
    """Start background monitoring for a service"""
    try:
        # In a production system, this would set up periodic health checks
        # For now, just log the monitoring start
        logger.info(f"Started monitoring for service {service_id}")
        
    except Exception as e:
        logger.error(f"Failed to start monitoring for service {service_id}: {str(e)}")

async def _perform_health_checks(db: Session):
    """Perform health checks on all services"""
    try:
        service_registry = ServiceV2Registry(db)
        health_statuses = await service_registry.health_check_services()
        
        online_count = sum(1 for status in health_statuses.values() if status.status == ServiceV2Status.ONLINE)
        total_count = len(health_statuses)
        
        logger.info(f"Health check completed: {online_count}/{total_count} services online")
        
    except Exception as e:
        logger.error(f"Health check batch failed: {str(e)}")