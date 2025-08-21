"""
Capability Matcher - Intelligent matching of tasks to services based on capabilities
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from ..models.enhanced_models import ServiceV2, TaskTemplateV2, ServiceV2Capability
from ..models.database import Task

logger = logging.getLogger(__name__)

class MatchQuality(Enum):
    """Quality of capability match"""
    PERFECT = "perfect"      # All required + all optional capabilities
    EXCELLENT = "excellent"  # All required + most optional capabilities  
    GOOD = "good"           # All required + some optional capabilities
    ADEQUATE = "adequate"   # All required capabilities only
    POOR = "poor"          # Missing some required capabilities
    INCOMPATIBLE = "incompatible"  # Missing critical required capabilities

@dataclass
class TaskRequirements:
    """Task execution requirements"""
    task_type: str
    required_capabilities: List[str]
    optional_capabilities: List[str] = None
    resource_requirements: Dict[str, Any] = None
    performance_requirements: Dict[str, Any] = None
    constraints: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.optional_capabilities is None:
            self.optional_capabilities = []
        if self.resource_requirements is None:
            self.resource_requirements = {}
        if self.performance_requirements is None:
            self.performance_requirements = {}
        if self.constraints is None:
            self.constraints = {}

@dataclass
class MatchScore:
    """Capability match scoring result"""
    service_id: int
    service_name: str
    quality: MatchQuality
    score: float  # 0.0 to 1.0
    required_match_rate: float  # Percentage of required capabilities met
    optional_match_rate: float  # Percentage of optional capabilities met
    capability_details: Dict[str, bool]  # Which capabilities are met
    confidence: float  # Confidence in this match (0.0 to 1.0)
    estimated_performance: Dict[str, Any] = None
    reasons: List[str] = None  # Reasons for score/quality
    
    def __post_init__(self):
        if self.estimated_performance is None:
            self.estimated_performance = {}
        if self.reasons is None:
            self.reasons = []

@dataclass
class ValidationResult:
    """ServiceV2 capability validation result"""
    is_valid: bool
    service_id: int
    task_id: Optional[int] = None
    errors: List[str] = None
    warnings: List[str] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.recommendations is None:
            self.recommendations = []

class CapabilityMatcher:
    """Advanced capability matching system for task-to-service assignment"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.capability_weights = {
            # Core analytical capabilities
            "hplc": 1.0,
            "gc": 1.0, 
            "ms": 1.0,
            "uv_detector": 0.8,
            "fluorescence_detector": 0.8,
            "autosampler": 0.7,
            "column_oven": 0.6,
            
            # Sample preparation capabilities
            "balance": 1.0,
            "pipette": 0.9,
            "vortex": 0.6,
            "centrifuge": 0.7,
            "heating": 0.7,
            "cooling": 0.7,
            "filtration": 0.8,
            "ph_measurement": 0.8,
            
            # General capabilities
            "data_processing": 0.5,
            "barcode_reading": 0.4,
            "temperature_control": 0.6,
            "pressure_monitoring": 0.5
        }

    def match_capabilities(self, 
                         requirements: TaskRequirements,
                         available_services: List[ServiceV2]) -> List[MatchScore]:
        """Score how well services match task requirements"""
        match_scores = []
        
        for service in available_services:
            score = self._calculate_match_score(service, requirements)
            match_scores.append(score)
        
        # Sort by score (descending) and quality
        match_scores.sort(key=lambda x: (x.score, x.confidence), reverse=True)
        
        logger.info(f"Matched {len(match_scores)} services for task type: {requirements.task_type}")
        return match_scores

    def find_alternative_services(self, 
                                primary_service: ServiceV2,
                                requirements: TaskRequirements,
                                all_services: List[ServiceV2]) -> List[ServiceV2]:
        """Find backup services when primary is unavailable"""
        alternatives = []
        
        # Remove primary service from candidates
        candidates = [s for s in all_services if s.id != primary_service.id]
        
        # Get match scores for alternatives
        match_scores = self.match_capabilities(requirements, candidates)
        
        # Only include services with adequate or better match quality
        adequate_matches = [
            score for score in match_scores 
            if score.quality in [MatchQuality.PERFECT, MatchQuality.EXCELLENT, 
                               MatchQuality.GOOD, MatchQuality.ADEQUATE]
        ]
        
        # Convert back to service objects
        service_dict = {s.id: s for s in candidates}
        alternatives = [service_dict[score.service_id] for score in adequate_matches]
        
        logger.info(f"Found {len(alternatives)} alternative services for {primary_service.name}")
        return alternatives

    def validate_service_constraints(self, 
                                   service: ServiceV2,
                                   task: Optional[Task] = None,
                                   requirements: Optional[TaskRequirements] = None) -> ValidationResult:
        """Validate if service can actually handle the task"""
        errors = []
        warnings = []
        recommendations = []
        
        try:
            # Basic availability check
            if not service.is_available():
                if service.current_load >= service.max_concurrent_tasks:
                    errors.append(f"ServiceV2 {service.name} is at maximum capacity ({service.current_load}/{service.max_concurrent_tasks})")
                elif service.status != service.status.ONLINE:
                    errors.append(f"ServiceV2 {service.name} is not online (status: {service.status})")
            
            # Check maintenance window
            if service.maintenance_window:
                current_time = datetime.utcnow()
                if self._is_in_maintenance_window(current_time, service.maintenance_window):
                    warnings.append(f"ServiceV2 {service.name} is in maintenance window")
            
            # Validate requirements if provided
            if requirements:
                # Check required capabilities
                service_caps = set((service.capabilities or {}).keys())
                required_caps = set(requirements.required_capabilities)
                missing_required = required_caps - service_caps
                
                if missing_required:
                    errors.append(f"ServiceV2 {service.name} missing required capabilities: {list(missing_required)}")
                
                # Check resource requirements
                if requirements.resource_requirements:
                    resource_errors = self._validate_resource_requirements(
                        service, requirements.resource_requirements
                    )
                    errors.extend(resource_errors)
                
                # Check performance requirements
                if requirements.performance_requirements:
                    perf_warnings = self._validate_performance_requirements(
                        service, requirements.performance_requirements
                    )
                    warnings.extend(perf_warnings)
                
                # Generate recommendations
                optional_caps = set(requirements.optional_capabilities) - service_caps
                if optional_caps:
                    recommendations.append(
                        f"Consider services with optional capabilities: {list(optional_caps)}"
                    )
            
            # Task-specific validation
            if task:
                task_errors, task_warnings = self._validate_task_specific_constraints(service, task)
                errors.extend(task_errors)
                warnings.extend(task_warnings)
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                service_id=service.id,
                task_id=task.id if task else None,
                errors=errors,
                warnings=warnings,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Validation failed for service {service.id}: {str(e)}")
            return ValidationResult(
                is_valid=False,
                service_id=service.id,
                task_id=task.id if task else None,
                errors=[f"Validation error: {str(e)}"]
            )

    def get_capability_recommendations(self, 
                                     task_type: str,
                                     current_services: List[ServiceV2]) -> Dict[str, Any]:
        """Get recommendations for improving capability coverage"""
        # Get task templates for this task type
        task_templates = self.db.query(TaskTemplateV2).filter(
            TaskTemplateV2.name.ilike(f"%{task_type}%")
        ).all()
        
        if not task_templates:
            return {"recommendations": [], "coverage_analysis": {}}
        
        # Analyze current capability coverage
        all_required_caps = set()
        all_optional_caps = set()
        
        for template in task_templates:
            all_required_caps.update(template.required_capabilities or [])
            all_optional_caps.update(template.optional_capabilities or [])
        
        # Check coverage by current services
        covered_caps = set()
        for service in current_services:
            if service.capabilities:
                covered_caps.update(service.capabilities.keys())
        
        missing_required = all_required_caps - covered_caps
        missing_optional = all_optional_caps - covered_caps
        
        recommendations = []
        
        if missing_required:
            recommendations.append({
                "type": "critical",
                "message": f"Missing critical capabilities: {list(missing_required)}",
                "action": "Add services with these capabilities"
            })
        
        if missing_optional:
            recommendations.append({
                "type": "enhancement", 
                "message": f"Missing optional capabilities: {list(missing_optional)}",
                "action": "Consider adding services for improved performance"
            })
        
        coverage_analysis = {
            "required_coverage": (len(all_required_caps - missing_required) / len(all_required_caps)) * 100 if all_required_caps else 100,
            "optional_coverage": (len(all_optional_caps - missing_optional) / len(all_optional_caps)) * 100 if all_optional_caps else 100,
            "total_capabilities": len(all_required_caps | all_optional_caps),
            "covered_capabilities": len(covered_caps & (all_required_caps | all_optional_caps))
        }
        
        return {
            "recommendations": recommendations,
            "coverage_analysis": coverage_analysis,
            "missing_required": list(missing_required),
            "missing_optional": list(missing_optional)
        }

    # Private methods
    
    def _calculate_match_score(self, service: ServiceV2, requirements: TaskRequirements) -> MatchScore:
        """Calculate detailed match score for a service"""
        service_caps = set((service.capabilities or {}).keys())
        required_caps = set(requirements.required_capabilities)
        optional_caps = set(requirements.optional_capabilities)
        
        # Calculate required capability match rate
        required_matches = required_caps & service_caps
        required_match_rate = len(required_matches) / len(required_caps) if required_caps else 1.0
        
        # Calculate optional capability match rate
        optional_matches = optional_caps & service_caps
        optional_match_rate = len(optional_matches) / len(optional_caps) if optional_caps else 1.0
        
        # Build capability details
        capability_details = {}
        for cap in required_caps | optional_caps:
            capability_details[cap] = cap in service_caps
        
        # Calculate weighted score
        base_score = required_match_rate * 0.8 + optional_match_rate * 0.2
        
        # Apply capability weights
        weighted_score = self._apply_capability_weights(
            service_caps, required_caps | optional_caps, base_score
        )
        
        # Determine quality
        quality = self._determine_match_quality(required_match_rate, optional_match_rate)
        
        # Calculate confidence based on service performance history
        confidence = self._calculate_confidence(service, requirements)
        
        # Generate reasons
        reasons = self._generate_match_reasons(
            service, required_matches, optional_matches, required_caps, optional_caps
        )
        
        return MatchScore(
            service_id=service.id,
            service_name=service.name,
            quality=quality,
            score=weighted_score,
            required_match_rate=required_match_rate,
            optional_match_rate=optional_match_rate,
            capability_details=capability_details,
            confidence=confidence,
            reasons=reasons
        )

    def _apply_capability_weights(self, 
                                service_caps: set,
                                task_caps: set,
                                base_score: float) -> float:
        """Apply capability importance weights to score"""
        if not task_caps:
            return base_score
        
        total_weight = sum(self.capability_weights.get(cap, 0.5) for cap in task_caps)
        matched_weight = sum(self.capability_weights.get(cap, 0.5) 
                           for cap in task_caps if cap in service_caps)
        
        weight_factor = matched_weight / total_weight if total_weight > 0 else 1.0
        return base_score * weight_factor

    def _determine_match_quality(self, 
                               required_rate: float, 
                               optional_rate: float) -> MatchQuality:
        """Determine match quality based on capability match rates"""
        if required_rate < 0.8:
            return MatchQuality.INCOMPATIBLE
        elif required_rate < 1.0:
            return MatchQuality.POOR
        elif optional_rate == 1.0:
            return MatchQuality.PERFECT
        elif optional_rate >= 0.8:
            return MatchQuality.EXCELLENT
        elif optional_rate >= 0.5:
            return MatchQuality.GOOD
        else:
            return MatchQuality.ADEQUATE

    def _calculate_confidence(self, service: ServiceV2, requirements: TaskRequirements) -> float:
        """Calculate confidence in the match based on service history"""
        # Base confidence
        confidence = 0.7
        
        # Increase confidence for services with good performance history
        from ..models.enhanced_models import ServiceV2PerformanceMetric
        perf_metrics = self.db.query(ServiceV2PerformanceMetric).filter(
            ServiceV2PerformanceMetric.service_id == service.id
        ).order_by(ServiceV2PerformanceMetric.recorded_at.desc()).first()
        
        if perf_metrics:
            if perf_metrics.success_rate:
                confidence += float(perf_metrics.success_rate) * 0.2
            if perf_metrics.uptime_percentage:
                confidence += float(perf_metrics.uptime_percentage) * 0.1
        
        # Increase confidence for recently active services
        if service.last_heartbeat:
            from datetime import datetime, timedelta
            time_since_heartbeat = datetime.utcnow() - service.last_heartbeat
            if time_since_heartbeat < timedelta(minutes=5):
                confidence += 0.1
        
        return min(confidence, 1.0)

    def _generate_match_reasons(self, 
                              service: ServiceV2,
                              required_matches: set,
                              optional_matches: set,
                              required_caps: set,
                              optional_caps: set) -> List[str]:
        """Generate human-readable reasons for the match score"""
        reasons = []
        
        # Required capabilities
        if required_matches == required_caps:
            reasons.append("All required capabilities are supported")
        else:
            missing = required_caps - required_matches
            reasons.append(f"Missing required capabilities: {list(missing)}")
        
        # Optional capabilities
        if optional_matches:
            reasons.append(f"Supports {len(optional_matches)}/{len(optional_caps)} optional capabilities")
        
        # ServiceV2 status
        if service.is_available():
            reasons.append("ServiceV2 is currently available")
        else:
            reasons.append(f"ServiceV2 busy ({service.current_load}/{service.max_concurrent_tasks})")
        
        # Performance notes
        if service.priority < 5:
            reasons.append("High priority service")
        
        if service.cost_per_hour:
            reasons.append(f"Cost: ${service.cost_per_hour}/hour")
        
        return reasons

    def _validate_resource_requirements(self, 
                                      service: ServiceV2,
                                      resource_reqs: Dict[str, Any]) -> List[str]:
        """Validate service meets resource requirements"""
        errors = []
        service_config = service.configuration or {}
        
        for resource, requirement in resource_reqs.items():
            if resource == "memory" and "available_memory" in service_config:
                available = service_config["available_memory"]
                if self._parse_memory_size(available) < self._parse_memory_size(requirement):
                    errors.append(f"Insufficient memory: need {requirement}, have {available}")
            
            elif resource == "cpu" and "cpu_cores" in service_config:
                available = service_config["cpu_cores"]
                if available < requirement:
                    errors.append(f"Insufficient CPU: need {requirement} cores, have {available}")
        
        return errors

    def _validate_performance_requirements(self, 
                                         service: ServiceV2,
                                         perf_reqs: Dict[str, Any]) -> List[str]:
        """Validate service meets performance requirements"""
        warnings = []
        
        from ..models.enhanced_models import ServiceV2PerformanceMetric
        perf_metrics = self.db.query(ServiceV2PerformanceMetric).filter(
            ServiceV2PerformanceMetric.service_id == service.id
        ).order_by(ServiceV2PerformanceMetric.recorded_at.desc()).first()
        
        if not perf_metrics:
            warnings.append("No performance history available for this service")
            return warnings
        
        if "max_duration_seconds" in perf_reqs:
            max_duration = perf_reqs["max_duration_seconds"]
            if perf_metrics.average_duration_seconds > max_duration:
                warnings.append(f"ServiceV2 may exceed time requirement: avg {perf_metrics.average_duration_seconds}s > {max_duration}s")
        
        if "min_success_rate" in perf_reqs:
            min_success = perf_reqs["min_success_rate"]
            if perf_metrics.success_rate < min_success:
                warnings.append(f"ServiceV2 success rate below requirement: {perf_metrics.success_rate} < {min_success}")
        
        return warnings

    def _validate_task_specific_constraints(self, 
                                          service: ServiceV2,
                                          task: Task) -> Tuple[List[str], List[str]]:
        """Validate task-specific constraints"""
        errors = []
        warnings = []
        
        # Check if task parameters are compatible with service
        if task.service_parameters and service.configuration:
            service_limits = service.configuration.get("parameter_limits", {})
            
            for param, value in task.service_parameters.items():
                if param in service_limits:
                    limits = service_limits[param]
                    if "min" in limits and value < limits["min"]:
                        errors.append(f"Parameter {param} below service minimum: {value} < {limits['min']}")
                    if "max" in limits and value > limits["max"]:
                        errors.append(f"Parameter {param} above service maximum: {value} > {limits['max']}")
        
        return errors, warnings

    def _is_in_maintenance_window(self, 
                                current_time: datetime,
                                maintenance_window: Dict[str, Any]) -> bool:
        """Check if current time is in maintenance window"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated scheduling logic
        return False

    def _parse_memory_size(self, size_str: str) -> int:
        """Parse memory size string to bytes"""
        if isinstance(size_str, (int, float)):
            return int(size_str)
        
        size_str = size_str.upper().strip()
        multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                return int(float(size_str[:-2]) * multiplier)
        
        # Assume bytes if no suffix
        return int(size_str)