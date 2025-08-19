#!/usr/bin/env python3
"""
Sample Preparation Task
Executes sample preparation workflow step by communicating with Sample Prep Station
"""

import requests
import time
import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SamplePreparationTask:
    def __init__(self, instrument_url: str = "http://localhost:5002"):
        self.instrument_url = instrument_url
        self.task_id = None
        self.sample_id = None
        self.results = {}
        
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute sample preparation task
        
        Parameters:
        - sample_id: Unique identifier for the sample
        - volume: Sample volume in mL
        - dilution_factor: Dilution ratio
        - target_ph: Target pH for adjustment
        - timeout: Maximum time to wait for completion (seconds)
        """
        try:
            # Extract and validate parameters
            self.sample_id = parameters.get('sample_id', f'SAMPLE_{int(time.time())}')
            volume = float(parameters.get('volume', 10.0))
            dilution_factor = float(parameters.get('dilution_factor', 2.0))
            target_ph = float(parameters.get('target_ph', 7.0))
            timeout = int(parameters.get('timeout', 300))  # 5 minutes default
            
            logger.info(f"Starting sample preparation for {self.sample_id}")
            logger.info(f"Parameters: volume={volume}mL, dilution={dilution_factor}x, pH={target_ph}")
            
            # Step 1: Check instrument status
            if not self._check_instrument_ready():
                return self._create_error_result("Instrument not ready")
            
            # Step 2: Submit preparation request
            prep_response = self._submit_preparation_request(
                self.sample_id, volume, dilution_factor, target_ph
            )
            if not prep_response:
                return self._create_error_result("Failed to start preparation")
            
            # Step 3: Monitor progress until completion
            result = self._monitor_preparation(timeout)
            
            # Step 4: Collect results
            if result['status'] == 'completed':
                final_results = self._collect_results()
                if final_results:
                    result.update(final_results)
                    logger.info(f"Sample preparation completed successfully for {self.sample_id}")
                else:
                    result = self._create_error_result("Failed to retrieve results")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in sample preparation task: {str(e)}")
            return self._create_error_result(f"Task execution failed: {str(e)}")
    
    def _check_instrument_ready(self) -> bool:
        """Check if the sample prep station is ready"""
        try:
            response = requests.get(f"{self.instrument_url}/status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                instrument_status = status_data.get('status', 'unknown')
                logger.info(f"Instrument status: {instrument_status}")
                return instrument_status in ['idle', 'completed']
            else:
                logger.error(f"Failed to get instrument status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Cannot connect to instrument: {str(e)}")
            return False
    
    def _submit_preparation_request(self, sample_id: str, volume: float, 
                                   dilution_factor: float, target_ph: float) -> bool:
        """Submit preparation request to instrument"""
        try:
            payload = {
                'sample_id': sample_id,
                'volume': volume,
                'dilution_factor': dilution_factor,
                'target_ph': target_ph
            }
            
            response = requests.post(
                f"{self.instrument_url}/prepare", 
                json=payload, 
                timeout=15
            )
            
            if response.status_code == 202:
                response_data = response.json()
                logger.info(f"Preparation started: {response_data.get('message')}")
                estimated_time = response_data.get('estimated_time_seconds', 60)
                logger.info(f"Estimated completion time: {estimated_time} seconds")
                return True
            else:
                error_msg = response.json().get('error', 'Unknown error')
                logger.error(f"Failed to start preparation: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error submitting preparation request: {str(e)}")
            return False
    
    def _monitor_preparation(self, timeout: int) -> Dict[str, Any]:
        """Monitor preparation progress until completion"""
        start_time = time.time()
        last_status = None
        
        while (time.time() - start_time) < timeout:
            try:
                response = requests.get(f"{self.instrument_url}/status", timeout=10)
                if response.status_code == 200:
                    status_data = response.json()
                    current_status = status_data.get('status')
                    
                    # Log status changes
                    if current_status != last_status:
                        logger.info(f"Status changed to: {current_status}")
                        last_status = current_status
                        
                        # Log progress if available
                        if 'progress_percent' in status_data:
                            progress = status_data['progress_percent']
                            logger.info(f"Progress: {progress}%")
                    
                    # Check for completion
                    if current_status == 'completed':
                        elapsed_time = time.time() - start_time
                        return {
                            'status': 'completed',
                            'message': 'Sample preparation completed successfully',
                            'execution_time_seconds': round(elapsed_time, 1),
                            'sample_id': self.sample_id
                        }
                    
                    # Check for errors
                    elif current_status in ['failed', 'aborted']:
                        return self._create_error_result(f"Preparation {current_status}")
                
                # Wait before next status check
                time.sleep(5)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error monitoring preparation: {str(e)}")
                time.sleep(10)  # Wait longer on connection errors
        
        # Timeout reached
        logger.error(f"Preparation timeout after {timeout} seconds")
        return self._create_error_result("Preparation timeout")
    
    def _collect_results(self) -> Optional[Dict[str, Any]]:
        """Collect final preparation results"""
        try:
            response = requests.get(f"{self.instrument_url}/results", timeout=10)
            if response.status_code == 200:
                results_data = response.json()
                self.results = results_data.get('results', {})
                
                # Format results for workflow system
                formatted_results = {
                    'preparation_results': self.results,
                    'sample_ready_for_analysis': True,
                    'prepared_sample_volume': self.results.get('actual_volume_ml'),
                    'sample_ph': self.results.get('actual_ph'),
                    'quality_status': self.results.get('quality_check'),
                    'recovery_percent': self.results.get('recovery_percent')
                }
                
                logger.info(f"Results collected: Recovery {self.results.get('recovery_percent')}%")
                return formatted_results
            else:
                logger.error(f"Failed to get results: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error collecting results: {str(e)}")
            return None
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            'status': 'failed',
            'error': error_message,
            'sample_id': self.sample_id,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Main execution function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python sample_preparation_task.py <parameters_json>")
        print("Example: python sample_preparation_task.py '{\"sample_id\":\"TEST001\",\"volume\":5.0,\"dilution_factor\":2.0,\"target_ph\":7.0}'")
        sys.exit(1)
    
    try:
        # Parse parameters from command line
        parameters_json = sys.argv[1]
        parameters = json.loads(parameters_json)
        
        # Create and execute task
        task = SamplePreparationTask()
        result = task.execute(parameters)
        
        # Output result as JSON
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result.get('status') == 'completed' else 1)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing parameters JSON: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error executing task: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()