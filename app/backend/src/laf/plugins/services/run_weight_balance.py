"""
Run Weight Balance Service Plugin

This plugin handles communication with the Weight Balance Service that coordinates
and processes materials data, preparing instructions for the physical weight balance instrument.
"""

import json
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from base import ServicePlugin, ExecutionResult


class RunWeightBalancePlugin(ServicePlugin):
    """Plugin for Run Weight Balance service coordination."""
    
    def __init__(self):
        super().__init__(
            name="Run Weight Balance", 
            endpoint="http://host.docker.internal:6001",
            version="1.0.0"
        )
    
    def execute(self, task_params: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the Run Weight Balance service task.
        
        This method is called by the workers and handles the complete service execution.
        """
        self.logger.info(f"Executing Run Weight Balance service")
        
        try:
            # Prepare the request data
            request_data = self.prepare_request_data(task_params, context)
            
            # Return the prepared data and let the workers handle the HTTP call
            # The workers will call process_response with the service response
            return ExecutionResult(
                success=True,
                data=request_data,
                status="ready_for_service_call"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to prepare Run Weight Balance request: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
                status="failed"
            )
    
    def prepare_request_data(self, task_params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the data to be sent to the Weight Balance Service.
        
        Extracts materials_table from previous tasks or uses provided parameters.
        """
        self.logger.info("Preparing request data for Run Weight Balance service")
        
        # Start with the task parameters
        request_data = dict(task_params)
        
        # Extract materials_table from previous Sample Measurement task if not provided
        if "materials_table" not in request_data or not request_data["materials_table"]:
            materials_table = self._extract_materials_from_context(context)
            if materials_table:
                request_data["materials_table"] = materials_table
                self.logger.info(f"Extracted materials_table from previous tasks: {materials_table}")
        
        # Ensure we have a materials_table
        if "materials_table" not in request_data:
            # Provide default materials table
            default_table = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
            request_data["materials_table"] = default_table
            self.logger.info(f"Using default materials_table: {default_table}")
        
        # Set default parameters if not provided
        request_data.setdefault("measurement_mode", "automatic")
        request_data.setdefault("stabilization_time", 3)
        request_data.setdefault("number_of_readings", 3)
        request_data.setdefault("output_format", "json")
        
        return request_data
    
    def _extract_materials_from_context(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract materials_table from previous task results in the context."""
        try:
            # Look for previous Sample Measurement task results
            previous_results = context.get("previous_task_results", [])
            
            for result in previous_results:
                task_name = result.get("task_name", "")
                if "Sample Measurement" in task_name:
                    task_data = result.get("data", {})
                    if "materials_table" in task_data:
                        return task_data["materials_table"]
            
            # Look in task parameters of previous tasks
            previous_tasks = context.get("previous_tasks", [])
            for task in previous_tasks:
                if "Sample Measurement" in task.get("name", ""):
                    params = task.get("service_parameters", {})
                    if isinstance(params, str):
                        params = json.loads(params) if params else {}
                    if "materials_table" in params:
                        return params["materials_table"]
            
        except Exception as e:
            self.logger.warning(f"Error extracting materials from context: {e}")
        
        return []
    
    def process_response(self, response_data: Dict[str, Any]) -> ExecutionResult:
        """
        Process the response from the Weight Balance Service.
        
        Args:
            response_data: Raw response from the service
            
        Returns:
            ExecutionResult: Processed result with standardized format
        """
        self.logger.info("Processing Run Weight Balance service response")
        
        try:
            # Validate the response
            if not response_data.get("success", False):
                error_msg = response_data.get("error", "Service reported failure")
                return ExecutionResult(
                    success=False,
                    error_message=error_msg,
                    status="failed"
                )
            
            # Extract and structure the results
            processed_data = {
                "service": "Weight Balance Service",
                "success": True,
                "timestamp": response_data.get("timestamp"),
                "results": response_data.get("results", []),
                "total_runs": response_data.get("total_runs", 0),
                "total_measurements": response_data.get("total_measurements", 0),
                "success_rate": response_data.get("success_rate", 0.0),
                "processing_mode": response_data.get("processing_mode", "automatic"),
                "stabilization_time": response_data.get("stabilization_time", 3),
                "measurements_per_sample": response_data.get("measurements_per_sample", 3)
            }
            
            self.logger.info(f"Run Weight Balance completed: {processed_data['total_measurements']} measurements, {processed_data['success_rate']}% success rate")
            
            return ExecutionResult(
                success=True,
                data=processed_data,
                status="completed"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process Run Weight Balance response: {e}")
            return ExecutionResult(
                success=False,
                error_message=f"Failed to process service response: {str(e)}",
                status="failed"
            )
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate Run Weight Balance service parameters."""
        # Check if we have materials_table or can extract it from context
        return True  # Validation handled in prepare_request_data
    
    def get_required_params(self) -> List[str]:
        """Get list of required parameters."""
        return []  # materials_table can be extracted from previous tasks
    
    def get_optional_params(self) -> List[str]:
        """Get list of optional parameters."""
        return [
            "materials_table",
            "measurement_mode",
            "stabilization_time", 
            "number_of_readings",
            "output_format"
        ]
    
    def get_action(self) -> str:
        """Get the service action path."""
        return "process_materials"
    
    def get_timeout(self) -> int:
        """Get the request timeout for this service."""
        return 120