"""
Base classes for the Laboratory Automation Framework plugin system.

This module defines the base classes that all task, service, and instrument plugins
must inherit from to ensure consistent behavior and scalability.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Enum defining the types of plugins supported by the system."""
    TASK = "task"
    SERVICE = "service"
    INSTRUMENT = "instrument"


class ExecutionResult:
    """Standardized result class for plugin execution."""
    
    def __init__(self, success: bool, data: Optional[Dict[str, Any]] = None, 
                 error_message: Optional[str] = None, status: str = "completed"):
        self.success = success
        self.data = data or {}
        self.error_message = error_message
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "error_message": self.error_message,
            "status": self.status
        }


class BasePlugin(ABC):
    """Base class for all plugins in the laboratory automation framework."""
    
    def __init__(self, name: str, plugin_type: PluginType, version: str = "1.0.0"):
        self.name = name
        self.plugin_type = plugin_type
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def execute(self, task_params: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the plugin with given parameters and context.
        
        Args:
            task_params: Parameters specific to this task execution
            context: Additional context including previous task results, workflow info, etc.
            
        Returns:
            ExecutionResult: Standardized result object
        """
        pass
    
    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate that the provided parameters are sufficient for execution.
        
        Args:
            params: Parameters to validate
            
        Returns:
            bool: True if parameters are valid
        """
        pass
    
    def get_required_params(self) -> List[str]:
        """
        Get list of required parameter names.
        
        Returns:
            List[str]: List of required parameter names
        """
        return []
    
    def get_optional_params(self) -> List[str]:
        """
        Get list of optional parameter names.
        
        Returns:
            List[str]: List of optional parameter names
        """
        return []
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get plugin metadata including name, type, version, and parameter schema.
        
        Returns:
            Dict[str, Any]: Plugin metadata
        """
        return {
            "name": self.name,
            "type": self.plugin_type.value,
            "version": self.version,
            "required_params": self.get_required_params(),
            "optional_params": self.get_optional_params()
        }


class TaskPlugin(BasePlugin):
    """Base class for task plugins (manual tasks requiring user interaction)."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        super().__init__(name, PluginType.TASK, version)
    
    @abstractmethod
    def get_completion_status(self, task_params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Determine the initial status for this task.
        
        Returns:
            str: Initial status ("pending", "awaiting_manual_completion", etc.)
        """
        pass
    
    def handle_manual_completion(self, task_params: Dict[str, Any], 
                                completion_data: Dict[str, Any]) -> ExecutionResult:
        """
        Handle manual completion of the task.
        
        Args:
            task_params: Original task parameters
            completion_data: Data provided by user when manually completing
            
        Returns:
            ExecutionResult: Result of manual completion
        """
        return ExecutionResult(
            success=True,
            data=completion_data,
            status="completed"
        )


class ServicePlugin(BasePlugin):
    """Base class for service plugins (HTTP services for data processing)."""
    
    def __init__(self, name: str, endpoint: str, version: str = "1.0.0"):
        super().__init__(name, PluginType.SERVICE, version)
        self.endpoint = endpoint
    
    @abstractmethod
    def prepare_request_data(self, task_params: Dict[str, Any], 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the data to be sent to the service endpoint.
        
        Args:
            task_params: Task-specific parameters
            context: Context including previous task results
            
        Returns:
            Dict[str, Any]: Data to send to service
        """
        pass
    
    @abstractmethod
    def process_response(self, response_data: Dict[str, Any]) -> ExecutionResult:
        """
        Process the response from the service and return standardized result.
        
        Args:
            response_data: Raw response from service
            
        Returns:
            ExecutionResult: Processed result
        """
        pass
    
    def get_endpoint(self) -> str:
        """Get the service endpoint URL."""
        return self.endpoint
    
    def get_action(self) -> str:
        """Get the action/path to append to the endpoint."""
        return ""
    
    def get_timeout(self) -> int:
        """Get the request timeout in seconds."""
        return 120


class InstrumentPlugin(BasePlugin):
    """Base class for instrument plugins (physical/simulated laboratory instruments)."""
    
    def __init__(self, name: str, endpoint: str, version: str = "1.0.0"):
        super().__init__(name, PluginType.INSTRUMENT, version)
        self.endpoint = endpoint
    
    @abstractmethod
    def prepare_instrument_data(self, task_params: Dict[str, Any], 
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the data to be sent to the instrument.
        
        Args:
            task_params: Task-specific parameters
            context: Context including previous task results
            
        Returns:
            Dict[str, Any]: Data to send to instrument
        """
        pass
    
    @abstractmethod
    def process_instrument_response(self, response_data: Dict[str, Any]) -> ExecutionResult:
        """
        Process the response from the instrument and return standardized result.
        
        Args:
            response_data: Raw response from instrument
            
        Returns:
            ExecutionResult: Processed result
        """
        pass
    
    def get_endpoint(self) -> str:
        """Get the instrument endpoint URL."""
        return self.endpoint
    
    def get_action(self) -> str:
        """Get the action/path to append to the endpoint."""
        return ""
    
    def get_timeout(self) -> int:
        """Get the request timeout in seconds."""
        return 300
    
    def reset_instrument(self) -> bool:
        """
        Reset the instrument before execution.
        
        Returns:
            bool: True if reset successful, False otherwise
        """
        return True
    
    def should_monitor_async(self) -> bool:
        """
        Determine if this instrument requires asynchronous monitoring.
        
        Returns:
            bool: True if async monitoring needed
        """
        return True