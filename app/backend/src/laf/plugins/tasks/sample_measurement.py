"""
Sample Measurement Task Plugin

This plugin handles manual data entry by laboratory scientists to define
what materials need to be measured/weighed in subsequent workflow steps.
"""

from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from base import TaskPlugin, ExecutionResult


class SampleMeasurementPlugin(TaskPlugin):
    """Plugin for Sample Measurement manual tasks."""
    
    def __init__(self):
        super().__init__(name="Sample Measurement", version="1.0.0")
    
    def execute(self, task_params: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the Sample Measurement task.
        
        For manual tasks, this sets up the task for manual completion.
        """
        self.logger.info(f"Setting up Sample Measurement task for manual completion")
        
        return ExecutionResult(
            success=True,
            data={
                "message": "Task awaiting manual completion by scientist",
                "requires_user_input": True
            },
            status="awaiting_manual_completion"
        )
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate Sample Measurement parameters."""
        # Basic validation - can be extended with specific requirements
        return True
    
    def get_completion_status(self, task_params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Return the initial status for Sample Measurement tasks."""
        return "awaiting_manual_completion"
    
    def get_required_params(self) -> List[str]:
        """Get list of required parameters for Sample Measurement."""
        return []  # No required params for basic sample measurement
    
    def get_optional_params(self) -> List[str]:
        """Get list of optional parameters for Sample Measurement."""
        return [
            "measurement_unit",
            "tolerance",
            "materials_table",
            "sample_type",
            "analyst_name",
            "notes"
        ]
    
    def handle_manual_completion(self, task_params: Dict[str, Any], 
                                completion_data: Dict[str, Any]) -> ExecutionResult:
        """
        Handle manual completion of Sample Measurement.
        
        Args:
            task_params: Original task parameters
            completion_data: Data provided by user (user_name, completion_notes, etc.)
            
        Returns:
            ExecutionResult: Result of manual completion
        """
        self.logger.info(f"Sample Measurement completed manually by {completion_data.get('user_name', 'unknown')}")
        
        # Process and structure the completion data
        result_data = {
            "completed_by": completion_data.get("user_name"),
            "completion_notes": completion_data.get("completion_notes"),
            "completion_method": "manual",
            "measurement_unit": task_params.get("measurement_unit", "g"),
            "tolerance": task_params.get("tolerance", 1.0)
        }
        
        # If materials table was provided, include it
        if "materials_table" in task_params:
            result_data["materials_table"] = task_params["materials_table"]
        
        return ExecutionResult(
            success=True,
            data=result_data,
            status="completed"
        )