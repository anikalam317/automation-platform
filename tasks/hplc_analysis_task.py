#!/usr/bin/env python3
"""
HPLC Analysis Task
Executes HPLC analysis workflow step by communicating with HPLC System
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

class HPLCAnalysisTask:
    def __init__(self, instrument_url: str = "http://localhost:5003"):
        self.instrument_url = instrument_url
        self.task_id = None
        self.sample_id = None
        self.results = {}
        
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute HPLC analysis task
        
        Parameters:
        - sample_id: Unique identifier for the sample
        - method: Analysis method name
        - injection_volume: Injection volume in µL
        - runtime_minutes: Analysis runtime in minutes
        - timeout: Maximum time to wait for completion (seconds)
        """
        try:
            # Extract and validate parameters
            self.sample_id = parameters.get('sample_id', f'SAMPLE_{int(time.time())}')
            method = parameters.get('method', 'USP_assay_method')
            injection_volume = float(parameters.get('injection_volume', 10.0))
            runtime_minutes = float(parameters.get('runtime_minutes', 20.0))
            timeout = int(parameters.get('timeout', 1800))  # 30 minutes default
            
            logger.info(f"Starting HPLC analysis for {self.sample_id}")
            logger.info(f"Parameters: method={method}, injection={injection_volume}µL, runtime={runtime_minutes}min")
            
            # Step 1: Check instrument status
            if not self._check_instrument_ready():
                return self._create_error_result("HPLC system not ready")
            
            # Step 2: Submit analysis request
            analysis_response = self._submit_analysis_request(
                self.sample_id, method, injection_volume, runtime_minutes
            )
            if not analysis_response:
                return self._create_error_result("Failed to start analysis")
            
            # Step 3: Monitor progress until completion
            result = self._monitor_analysis(timeout)
            
            # Step 4: Collect results and perform data analysis
            if result['status'] == 'completed':
                final_results = self._collect_results()
                if final_results:
                    result.update(final_results)
                    # Perform quality assessment
                    quality_assessment = self._assess_data_quality(final_results)
                    result['quality_assessment'] = quality_assessment
                    logger.info(f"HPLC analysis completed successfully for {self.sample_id}")
                else:
                    result = self._create_error_result("Failed to retrieve analysis results")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in HPLC analysis task: {str(e)}")
            return self._create_error_result(f"Task execution failed: {str(e)}")
    
    def _check_instrument_ready(self) -> bool:
        """Check if the HPLC system is ready"""
        try:
            response = requests.get(f"{self.instrument_url}/status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                instrument_status = status_data.get('status', 'unknown')
                
                # Additional checks for HPLC readiness
                lamp_status = status_data.get('lamp_status', 'unknown')
                autosampler_ready = status_data.get('autosampler_ready', False)
                
                logger.info(f"HPLC status: {instrument_status}, lamp: {lamp_status}, autosampler: {autosampler_ready}")
                
                is_ready = (
                    instrument_status in ['idle', 'completed'] and
                    lamp_status == 'on' and
                    autosampler_ready
                )
                
                if not is_ready:
                    logger.warning("HPLC system not fully ready for analysis")
                
                return is_ready
            else:
                logger.error(f"Failed to get HPLC status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Cannot connect to HPLC system: {str(e)}")
            return False
    
    def _submit_analysis_request(self, sample_id: str, method: str, 
                                injection_volume: float, runtime_minutes: float) -> bool:
        """Submit analysis request to HPLC system"""
        try:
            payload = {
                'sample_id': sample_id,
                'method': method,
                'injection_volume': injection_volume,
                'runtime_minutes': runtime_minutes
            }
            
            response = requests.post(
                f"{self.instrument_url}/analyze", 
                json=payload, 
                timeout=15
            )
            
            if response.status_code == 202:
                response_data = response.json()
                logger.info(f"Analysis started: {response_data.get('message')}")
                estimated_time = response_data.get('estimated_total_time_seconds', 1200)
                logger.info(f"Estimated completion time: {estimated_time} seconds")
                return True
            else:
                error_msg = response.json().get('error', 'Unknown error')
                logger.error(f"Failed to start analysis: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error submitting analysis request: {str(e)}")
            return False
    
    def _monitor_analysis(self, timeout: int) -> Dict[str, Any]:
        """Monitor analysis progress until completion"""
        start_time = time.time()
        last_status = None
        last_progress = None
        
        while (time.time() - start_time) < timeout:
            try:
                response = requests.get(f"{self.instrument_url}/status", timeout=10)
                if response.status_code == 200:
                    status_data = response.json()
                    current_status = status_data.get('status')
                    current_progress = status_data.get('progress_percent')
                    
                    # Log status changes
                    if current_status != last_status:
                        logger.info(f"Analysis status: {current_status}")
                        last_status = current_status
                    
                    # Log progress updates
                    if current_progress and current_progress != last_progress:
                        if current_progress - (last_progress or 0) >= 10:  # Log every 10% progress
                            logger.info(f"Analysis progress: {current_progress}%")
                            last_progress = current_progress
                    
                    # Log pressure monitoring during run
                    if current_status == 'running' and 'pressure_bar' in status_data:
                        pressure = status_data['pressure_bar']
                        if pressure > 250:  # High pressure warning
                            logger.warning(f"High pressure detected: {pressure} bar")
                    
                    # Check for completion
                    if current_status == 'completed':
                        elapsed_time = time.time() - start_time
                        return {
                            'status': 'completed',
                            'message': 'HPLC analysis completed successfully',
                            'execution_time_seconds': round(elapsed_time, 1),
                            'sample_id': self.sample_id
                        }
                    
                    # Check for errors
                    elif current_status in ['failed', 'aborted']:
                        return self._create_error_result(f"Analysis {current_status}")
                
                # Wait before next status check
                time.sleep(10)  # Longer interval for HPLC monitoring
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error monitoring analysis: {str(e)}")
                time.sleep(15)  # Wait longer on connection errors
        
        # Timeout reached
        logger.error(f"Analysis timeout after {timeout} seconds")
        return self._create_error_result("Analysis timeout")
    
    def _collect_results(self) -> Optional[Dict[str, Any]]:
        """Collect final analysis results"""
        try:
            response = requests.get(f"{self.instrument_url}/results", timeout=10)
            if response.status_code == 200:
                results_data = response.json()
                self.results = results_data.get('results', {})
                
                # Extract key analytical data
                peaks = self.results.get('peaks', [])
                summary = self.results.get('summary', {})
                quality_assessment = self.results.get('quality_assessment', {})
                
                # Format results for workflow system
                formatted_results = {
                    'analysis_results': self.results,
                    'sample_id': self.sample_id,
                    'method_used': self.results.get('method'),
                    'analysis_completed': self.results.get('analysis_completed'),
                    'main_compound_purity': summary.get('main_compound_purity'),
                    'total_impurities': summary.get('total_impurities'),
                    'number_of_peaks': len(peaks),
                    'specification_compliance': quality_assessment.get('passes_specification', False),
                    'system_suitability': quality_assessment.get('system_suitability'),
                    'chromatogram_file': self.results.get('chromatogram_file'),
                    'peak_data': [
                        {
                            'compound': peak.get('compound'),
                            'retention_time': peak.get('retention_time'),
                            'purity_percent': peak.get('purity_percent')
                        }
                        for peak in peaks
                    ]
                }
                
                purity = summary.get('main_compound_purity', 0)
                logger.info(f"Analysis results: {purity}% purity, {len(peaks)} peaks detected")
                return formatted_results
            else:
                logger.error(f"Failed to get analysis results: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error collecting results: {str(e)}")
            return None
    
    def _assess_data_quality(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform additional quality assessment on analysis results"""
        try:
            analysis_results = results.get('analysis_results', {})
            summary = analysis_results.get('summary', {})
            quality_assessment = analysis_results.get('quality_assessment', {})
            
            # Extract quality metrics
            resolution = summary.get('resolution', 0)
            theoretical_plates = summary.get('theoretical_plates', 0)
            baseline_noise = summary.get('baseline_noise', 0)
            main_purity = summary.get('main_compound_purity', 0)
            
            # Perform quality checks
            quality_checks = {
                'resolution_acceptable': resolution >= 2.0,
                'column_efficiency_good': theoretical_plates >= 5000,
                'baseline_noise_low': baseline_noise <= 2.0,
                'purity_within_spec': main_purity >= 98.0,
                'system_suitability_passed': quality_assessment.get('system_suitability') == 'passed'
            }
            
            # Overall assessment
            all_checks_passed = all(quality_checks.values())
            critical_checks = ['resolution_acceptable', 'purity_within_spec', 'system_suitability_passed']
            critical_passed = all(quality_checks[check] for check in critical_checks)
            
            overall_rating = 'excellent' if all_checks_passed else ('good' if critical_passed else 'poor')
            
            assessment = {
                'overall_rating': overall_rating,
                'data_quality_score': sum(quality_checks.values()) / len(quality_checks) * 100,
                'quality_checks': quality_checks,
                'recommendations': []
            }
            
            # Generate recommendations
            if not quality_checks['resolution_acceptable']:
                assessment['recommendations'].append('Consider optimizing mobile phase gradient')
            if not quality_checks['column_efficiency_good']:
                assessment['recommendations'].append('Column may need replacement or regeneration')
            if not quality_checks['baseline_noise_low']:
                assessment['recommendations'].append('Check detector lamp and flow cell')
            if not quality_checks['purity_within_spec']:
                assessment['recommendations'].append('Sample may not meet specification requirements')
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {str(e)}")
            return {'overall_rating': 'unknown', 'error': str(e)}
    
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
        print("Usage: python hplc_analysis_task.py <parameters_json>")
        print("Example: python hplc_analysis_task.py '{\"sample_id\":\"TEST001\",\"method\":\"USP_assay_method\",\"injection_volume\":10.0,\"runtime_minutes\":20.0}'")
        sys.exit(1)
    
    try:
        # Parse parameters from command line
        parameters_json = sys.argv[1]
        parameters = json.loads(parameters_json)
        
        # Create and execute task
        task = HPLCAnalysisTask()
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