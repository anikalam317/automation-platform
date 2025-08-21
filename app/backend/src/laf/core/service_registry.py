"""
Service Registry - Centralized service discovery and management system
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from dataclasses import dataclass
from enum import Enum

from ..models.enhanced_models import (
    ServiceV2, ServiceStatus, ServiceCapability, ServicePerformanceMetric,
    UserServicePreference
)
from ..models.database import get_db
import httpx

logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for registering a new service"""
    name: str
    type: str
    category: str
    endpoint: str
    health_check_endpoint: Optional[str] = None
    capabilities: Dict[str, Any] = None
    max_concurrent_tasks: int = 1
    priority: int = 5
    location: Optional[str] = None
    configuration: Dict[str, Any] = None
    service_metadata: Dict[str, Any] = None
    cost_per_hour: Optional[float] = None

@dataclass
class LoadMetrics:
    """Service load metrics"""
    service_id: int
    current_load: int
    max_concurrent_tasks: int
    load_percentage: float
    average_response_time: float
    success_rate: float
    uptime_percentage: float

@dataclass
class HealthStatus:
    """Service health status"""
    service_id: int
    status: ServiceStatus
    last_heartbeat: Optional[datetime]
    response_time_ms: Optional[float]
    error_message: Optional[str] = None

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RESPONSE_TIME = "response_time"
    CAPABILITY_WEIGHTED = "capability_weighted"
    COST_OPTIMIZED = "cost_optimized"
    USER_PREFERENCE = "user_preference"

class ServiceRegistry:
    """Centralized service registry with health monitoring and load balancing"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.health_check_interval = 30  # seconds
        self.health_check_timeout = 5  # seconds
        self._round_robin_counters = {}
        
    async def register_service(self, config: ServiceConfig) -> Service:
        """Register a new service with capabilities"""
        try:
            # Create service record
            service = ServiceV2(
                name=config.name,
                type=config.type,
                category=config.category,
                endpoint=config.endpoint,
                health_check_endpoint=config.health_check_endpoint or f"{config.endpoint}/status",
                max_concurrent_tasks=config.max_concurrent_tasks,
                priority=config.priority,
                location=config.location,
                capabilities=config.capabilities or {},
                configuration=config.configuration or {},
                service_metadata=config.service_metadata or {},
                cost_per_hour=config.cost_per_hour,
                status=ServiceStatus.OFFLINE,
                current_load=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(service)
            self.db.flush()  # Get the service ID
            
            # Register individual capabilities
            if config.capabilities:
                for capability_name, capability_value in config.capabilities.items():
                    capability = ServiceCapability(
                        service_id=service.id,
                        capability_name=capability_name,
                        capability_value=capability_value if isinstance(capability_value, dict) else {"enabled": capability_value},
                        confidence_score=1.0
                    )
                    self.db.add(capability)
            
            self.db.commit()
            
            # Perform initial health check
            await self._health_check_service(service)
            
            logger.info(f"Registered service: {service.name} (ID: {service.id})")
            return service
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to register service {config.name}: {str(e)}")
            raise

    async def discover_services(self, 
                              required_capabilities: List[str],
                              optional_capabilities: List[str] = None,
                              constraints: Dict[str, Any] = None) -> List[Service]:
        """Find services matching required capabilities and constraints"""
        try:
            query = self.db.query(ServiceV2).filter(
                Service.status == ServiceStatus.ONLINE
            )
            
            # Filter by required capabilities
            if required_capabilities:
                for capability in required_capabilities:
                    query = query.filter(
                        Service.capabilities.op('?')(capability)
                    )
            
            # Apply additional constraints
            if constraints:
                if 'category' in constraints:
                    query = query.filter(Service.category == constraints['category'])
                if 'location' in constraints:
                    query = query.filter(Service.location == constraints['location'])
                if 'max_cost_per_hour' in constraints:
                    query = query.filter(
                        or_(Service.cost_per_hour.is_(None), 
                            Service.cost_per_hour <= constraints['max_cost_per_hour'])
                    )
                if 'min_priority' in constraints:
                    query = query.filter(Service.priority >= constraints['min_priority'])
            
            services = query.all()
            
            # Score services based on optional capabilities
            if optional_capabilities:
                for service in services:
                    service._capability_score = self._calculate_capability_score(
                        service, required_capabilities, optional_capabilities
                    )
                services.sort(key=lambda s: getattr(s, '_capability_score', 0), reverse=True)
            
            logger.info(f"Discovered {len(services)} services for capabilities: {required_capabilities}")
            return services
            
        except Exception as e:
            logger.error(f"Failed to discover services: {str(e)}")
            raise

    async def get_available_services(self, 
                                   task_type: Optional[str] = None,
                                   user_id: Optional[str] = None) -> List[Service]:
        """Get currently available services, optionally filtered by task type and user preferences"""
        try:
            query = self.db.query(ServiceV2).filter(
                and_(
                    Service.status == ServiceStatus.ONLINE,
                    Service.current_load < Service.max_concurrent_tasks
                )
            )
            
            services = query.all()
            
            # Apply user preferences if user_id provided
            if user_id:
                services = await self._apply_user_preferences(services, user_id, task_type)
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to get available services: {str(e)}")
            raise

    async def health_check_services(self) -> Dict[int, HealthStatus]:
        """Perform health check on all registered services"""
        services = self.db.query(ServiceV2).all()
        health_statuses = {}
        
        # Use asyncio to check multiple services concurrently
        tasks = [self._health_check_service(service) for service in services]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for service, result in zip(services, results):
            if isinstance(result, Exception):
                health_statuses[service.id] = HealthStatus(
                    service_id=service.id,
                    status=ServiceStatus.ERROR,
                    last_heartbeat=service.last_heartbeat,
                    response_time_ms=None,
                    error_message=str(result)
                )
            else:
                health_statuses[service.id] = result
        
        return health_statuses

    async def load_balance_selection(self, 
                                   candidates: List[ServiceV2], 
                                   strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED,
                                   task_context: Dict[str, Any] = None) -> Optional[ServiceV2]:
        """Select best service using specified load balancing strategy"""
        if not candidates:
            return None
        
        available_services = [s for s in candidates if s.is_available()]
        if not available_services:
            return None
        
        try:
            if strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._round_robin_selection(available_services)
            
            elif strategy == LoadBalancingStrategy.LEAST_LOADED:
                return min(available_services, key=lambda s: s.get_load_percentage())
            
            elif strategy == LoadBalancingStrategy.RESPONSE_TIME:
                return await self._response_time_selection(available_services)
            
            elif strategy == LoadBalancingStrategy.CAPABILITY_WEIGHTED:
                return self._capability_weighted_selection(available_services, task_context)
            
            elif strategy == LoadBalancingStrategy.COST_OPTIMIZED:
                return self._cost_optimized_selection(available_services)
            
            elif strategy == LoadBalancingStrategy.USER_PREFERENCE:
                return self._user_preference_selection(available_services, task_context)
            
            else:
                # Default to least loaded
                return min(available_services, key=lambda s: s.get_load_percentage())
                
        except Exception as e:
            logger.error(f"Load balancing failed with strategy {strategy}: {str(e)}")
            # Fallback to first available service
            return available_services[0]

    async def update_service_load(self, service_id: int, load_change: int) -> None:
        """Update service current load"""
        try:
            service = self.db.query(ServiceV2).filter(Service.id == service_id).first()
            if service:
                service.current_load = max(0, service.current_load + load_change)
                service.updated_at = datetime.utcnow()
                
                # Update status based on load
                if service.current_load >= service.max_concurrent_tasks:
                    service.status = ServiceStatus.BUSY
                elif service.status == ServiceStatus.BUSY and service.current_load < service.max_concurrent_tasks:
                    service.status = ServiceStatus.ONLINE
                
                self.db.commit()
                logger.debug(f"Updated service {service_id} load to {service.current_load}")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update service load: {str(e)}")

    async def get_service_metrics(self, service_id: int) -> Optional[LoadMetrics]:
        """Get comprehensive metrics for a service"""
        try:
            service = self.db.query(ServiceV2).filter(Service.id == service_id).first()
            if not service:
                return None
            
            # Get performance metrics
            perf_metric = self.db.query(ServicePerformanceMetric).filter(
                ServicePerformanceMetric.service_id == service_id
            ).order_by(ServicePerformanceMetric.recorded_at.desc()).first()
            
            return LoadMetrics(
                service_id=service.id,
                current_load=service.current_load,
                max_concurrent_tasks=service.max_concurrent_tasks,
                load_percentage=service.get_load_percentage(),
                average_response_time=float(perf_metric.average_duration_seconds) if perf_metric else 0.0,
                success_rate=float(perf_metric.success_rate) if perf_metric else 0.0,
                uptime_percentage=float(perf_metric.uptime_percentage) if perf_metric else 0.0
            )
            
        except Exception as e:
            logger.error(f"Failed to get service metrics: {str(e)}")
            return None

    # Private methods
    
    async def _health_check_service(self, service: Service) -> HealthStatus:
        """Perform health check on individual service"""
        start_time = datetime.utcnow()
        
        try:
            async with httpx.AsyncClient(timeout=self.health_check_timeout) as client:
                response = await client.get(service.health_check_endpoint)
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    service.status = ServiceStatus.ONLINE
                    service.last_heartbeat = datetime.utcnow()
                    self.db.commit()
                    
                    return HealthStatus(
                        service_id=service.id,
                        status=ServiceStatus.ONLINE,
                        last_heartbeat=service.last_heartbeat,
                        response_time_ms=response_time
                    )
                else:
                    service.status = ServiceStatus.ERROR
                    self.db.commit()
                    
                    return HealthStatus(
                        service_id=service.id,
                        status=ServiceStatus.ERROR,
                        last_heartbeat=service.last_heartbeat,
                        response_time_ms=response_time,
                        error_message=f"HTTP {response.status_code}"
                    )
                    
        except Exception as e:
            service.status = ServiceStatus.OFFLINE
            self.db.commit()
            
            return HealthStatus(
                service_id=service.id,
                status=ServiceStatus.OFFLINE,
                last_heartbeat=service.last_heartbeat,
                response_time_ms=None,
                error_message=str(e)
            )

    def _calculate_capability_score(self, 
                                  service: Service, 
                                  required: List[str], 
                                  optional: List[str]) -> float:
        """Calculate capability match score for a service"""
        score = 0.0
        service_caps = service.capabilities or {}
        
        # Required capabilities (must have all)
        required_score = sum(1.0 for cap in required if cap in service_caps)
        if len(required) > 0:
            required_score /= len(required)
        
        # Optional capabilities (bonus points)
        optional_score = sum(0.5 for cap in optional if cap in service_caps)
        if len(optional) > 0:
            optional_score /= len(optional)
        
        return required_score + optional_score

    def _round_robin_selection(self, services: List[ServiceV2]) -> Service:
        """Round-robin service selection"""
        service_ids = [s.id for s in services]
        service_key = tuple(sorted(service_ids))
        
        if service_key not in self._round_robin_counters:
            self._round_robin_counters[service_key] = 0
        
        index = self._round_robin_counters[service_key] % len(services)
        self._round_robin_counters[service_key] += 1
        
        return services[index]

    async def _response_time_selection(self, services: List[ServiceV2]) -> Service:
        """Select service with best average response time"""
        service_metrics = []
        
        for service in services:
            perf_metric = self.db.query(ServicePerformanceMetric).filter(
                ServicePerformanceMetric.service_id == service.id
            ).order_by(ServicePerformanceMetric.recorded_at.desc()).first()
            
            avg_duration = float(perf_metric.average_duration_seconds) if perf_metric else float('inf')
            service_metrics.append((service, avg_duration))
        
        return min(service_metrics, key=lambda x: x[1])[0]

    def _capability_weighted_selection(self, 
                                     services: List[ServiceV2], 
                                     task_context: Dict[str, Any]) -> Service:
        """Select service weighted by capability match"""
        if not task_context or 'required_capabilities' not in task_context:
            return services[0]
        
        required_caps = task_context['required_capabilities']
        optional_caps = task_context.get('optional_capabilities', [])
        
        scored_services = [
            (service, self._calculate_capability_score(service, required_caps, optional_caps))
            for service in services
        ]
        
        return max(scored_services, key=lambda x: x[1])[0]

    def _cost_optimized_selection(self, services: List[ServiceV2]) -> Service:
        """Select lowest cost service"""
        cost_services = [(s, s.cost_per_hour or 0.0) for s in services]
        return min(cost_services, key=lambda x: x[1])[0]

    def _user_preference_selection(self, 
                                 services: List[ServiceV2], 
                                 task_context: Dict[str, Any]) -> Service:
        """Select service based on user preferences"""
        if not task_context or 'user_id' not in task_context:
            return services[0]
        
        user_id = task_context['user_id']
        task_type = task_context.get('task_type')
        
        # Get user preferences
        pref_query = self.db.query(UserServicePreference).filter(
            UserServicePreference.user_id == user_id
        )
        
        if task_type:
            pref_query = pref_query.filter(
                or_(UserServicePreference.task_type == task_type,
                    UserServicePreference.task_type.is_(None))
            )
        
        preferences = pref_query.first()
        
        if preferences and preferences.preferred_service_ids:
            # Sort services by user preference order
            service_dict = {s.id: s for s in services}
            for service_id in preferences.preferred_service_ids:
                if service_id in service_dict:
                    return service_dict[service_id]
        
        # No preference found, use least loaded
        return min(services, key=lambda s: s.get_load_percentage())

    async def _apply_user_preferences(self, 
                                    services: List[ServiceV2], 
                                    user_id: str, 
                                    task_type: Optional[str] = None) -> List[Service]:
        """Apply user preferences to filter and sort services"""
        try:
            # Get user preferences
            pref_query = self.db.query(UserServicePreference).filter(
                UserServicePreference.user_id == user_id
            )
            
            if task_type:
                pref_query = pref_query.filter(
                    or_(UserServicePreference.task_type == task_type,
                        UserServicePreference.task_type.is_(None))
                )
            
            preferences = pref_query.first()
            
            if not preferences:
                return services
            
            # Filter out blacklisted services
            if preferences.blacklisted_service_ids:
                services = [s for s in services 
                           if s.id not in preferences.blacklisted_service_ids]
            
            # Sort by preference order if specified
            if preferences.preferred_service_ids:
                preferred_dict = {s.id: s for s in services 
                                if s.id in preferences.preferred_service_ids}
                other_services = [s for s in services 
                                if s.id not in preferences.preferred_service_ids]
                
                # Order preferred services according to user preference
                ordered_preferred = []
                for service_id in preferences.preferred_service_ids:
                    if service_id in preferred_dict:
                        ordered_preferred.append(preferred_dict[service_id])
                
                services = ordered_preferred + other_services
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to apply user preferences: {str(e)}")
            return services