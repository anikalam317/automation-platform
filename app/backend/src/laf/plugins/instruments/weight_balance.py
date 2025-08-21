"""
Weight Balance Instrument Plugin

This plugin handles communication with the Weight Balance instrument simulator
for executing physical dispensing and measurement operations.
"""

import json
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from base import InstrumentPlugin, ExecutionResult


class WeightBalancePlugin(InstrumentPlugin):
    """Plugin for Weight Balance instrument operations."""
    
    def __init__(self):
        super().__init__(
            name="Weight Balance", 
            endpoint="http://host.docker.internal:5011",
            version="1.0.0"
        )
    
    def execute(self, task_params: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the Weight Balance instrument task.
        
        This method is called by the workers and handles the complete instrument execution.
        """
        self.logger.info(f"Executing Weight Balance instrument")
        
        try:
            # Prepare the instrument data
            instrument_data = self.prepare_instrument_data(task_params, context)
            
            # Return the prepared data and let the workers handle the HTTP call
            # The workers will call process_instrument_response with the instrument response
            return ExecutionResult(
                success=True,
                data=instrument_data,
                status="ready_for_instrument_call"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to prepare Weight Balance instrument data: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
                status="failed"
            )
    
    def prepare_instrument_data(self, task_params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the data to be sent to the Weight Balance instrument.
        
        Extracts materials_table from previous Run Weight Balance service results.
        """
        self.logger.info("Preparing data for Weight Balance instrument")
        
        # Start with the task parameters
        instrument_data = dict(task_params)
        
        # Extract materials_table from previous Run Weight Balance service results
        if "materials_table" not in instrument_data or not instrument_data["materials_table"]:
            materials_table = self._extract_materials_from_service_results(context)
            if materials_table:
                instrument_data["materials_table"] = materials_table
                self.logger.info(f"Extracted materials_table from Run Weight Balance service: {materials_table}")
        
        # Ensure we have a materials_table
        if "materials_table" not in instrument_data:
            # Provide default materials table
            default_table = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
            instrument_data["materials_table"] = default_table
            self.logger.info(f"Using default materials_table: {default_table}")
        
        # Set default instrument parameters if not provided
        instrument_data.setdefault("unit", "g")
        instrument_data.setdefault("tolerance", 1.0)
        instrument_data.setdefault("replicates", 1)
        
        return instrument_data
    
    def _extract_materials_from_service_results(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract materials_table from Run Weight Balance service results."""
        try:
            # Look for previous Run Weight Balance service results
            previous_results = context.get("previous_task_results", [])
            
            for result in previous_results:
                task_name = result.get("task_name", "")
                if "Run Weight Balance" in task_name:
                    service_results = result.get("data", {})
                    
                    # Extract materials_table from service results
                    if "results" in service_results and service_results["results"]:
                        # Convert service results to materials table format
                        materials_table = []
                        for result_item in service_results["results"]:
                            if "run" in result_item and "materials" in result_item:
                                row = {"run": result_item["run"]}
                                for material in result_item["materials"]:
                                    material_name = material.get("material", "material_1")
                                    row[material_name] = material.get("target_weight", 0.1)
                                materials_table.append(row)
                        
                        if materials_table:
                            return materials_table
            
            # Look in database context if available
            database_context = context.get("database_results", [])
            for db_result in database_context:
                if "Run Weight Balance" in db_result.get("task_name", ""):
                    data = db_result.get("data", {})
                    if isinstance(data, str):
                        data = json.loads(data) if data else {}
                    
                    if "results" in data and data["results"]:
                        # Convert service results to materials table format
                        materials_table = []
                        for result_item in data["results"]:
                            if "run" in result_item and "materials" in result_item:
                                row = {"run": result_item["run"]}
                                for material in result_item["materials"]:
                                    material_name = material.get("material", "material_1")
                                    row[material_name] = material.get("target_weight", 0.1)
                                materials_table.append(row)
                        
                        if materials_table:
                            return materials_table
            
        except Exception as e:
            self.logger.warning(f"Error extracting materials from service results: {e}")
        
        return []
    
    def process_instrument_response(self, response_data: Dict[str, Any]) -> ExecutionResult:
        """
        Process the response from the Weight Balance instrument.
        
        Args:
            response_data: Raw response from the instrument
            
        Returns:
            ExecutionResult: Processed result with standardized format
        """
        self.logger.info("Processing Weight Balance instrument response")
        
        try:
            # Validate the response
            if not response_data.get("success", False):
                error_msg = response_data.get("error", "Instrument reported failure")
                return ExecutionResult(
                    success=False,
                    error_message=error_msg,
                    status="failed"
                )
            
            # Extract and structure the results
            processed_data = {
                "instrument": "Weight Balance",
                "success": True,
                "timestamp": response_data.get("timestamp"),
                "results": response_data.get("results", []),
                "total_runs": response_data.get("total_runs", 0),
                "total_measurements": response_data.get("total_measurements", 0),
                "successful_measurements": response_data.get("successful_measurements", 0),
                "success_rate": response_data.get("success_rate", 0.0)
            }
            
            self.logger.info(f"Weight Balance completed: {processed_data['total_measurements']} measurements, {processed_data['success_rate']}% success rate")
            
            return ExecutionResult(
                success=True,
                data=processed_data,
                status="completed"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process Weight Balance response: {e}")
            return ExecutionResult(
                success=False,
                error_message=f"Failed to process instrument response: {str(e)}",
                status="failed"
            )
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate Weight Balance instrument parameters."""
        # Check if we have materials_table or can extract it from context
        return True  # Validation handled in prepare_instrument_data
    
    def get_required_params(self) -> List[str]:
        """Get list of required parameters."""
        return []  # materials_table can be extracted from previous service results
    
    def get_optional_params(self) -> List[str]:
        """Get list of optional parameters."""
        return [
            "materials_table",
            "unit",
            "tolerance",
            "replicates",
            "instrument_id",
            "make",
            "model"
        ]
    
    def get_action(self) -> str:
        """Get the instrument action path."""
        return "dispense"
    
    def get_timeout(self) -> int:
        """Get the request timeout for this instrument."""
        return 300
    
    def reset_instrument(self) -> bool:
        """
        Indicate whether the instrument should be reset before execution.
        
        Returns:
            bool: True if reset should be performed
        """
        return True
    
    def should_monitor_async(self) -> bool:
        """
        Determine if this instrument requires asynchronous monitoring.
        
        Returns:
            bool: True if async monitoring is needed
        """
        return True