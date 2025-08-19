import Ajv, { ErrorObject } from 'ajv';
import workflowSchema from '../schemas/workflow_schema.json';
import { WorkflowCreate } from '../types/workflow';

// Initialize AJV 
const ajv = new Ajv({ allErrors: true });

// Compile the workflow schema
const validateWorkflow = ajv.compile(workflowSchema);

export interface ValidationResult {
  valid: boolean;
  errors?: ErrorObject[];
  formattedErrors?: string[];
}

/**
 * Validate a workflow against the JSON schema
 */
export function validateWorkflowData(workflow: WorkflowCreate): ValidationResult {
  const valid = validateWorkflow(workflow);
  
  if (!valid && validateWorkflow.errors) {
    const formattedErrors = validateWorkflow.errors.map(error => {
      const field = error.instancePath || error.schemaPath;
      const message = error.message || 'Invalid value';
      
      switch (error.keyword) {
        case 'required':
          return `Missing required field: ${error.params?.missingProperty}`;
        case 'minLength':
          return `${field} must be at least ${error.params?.limit} characters`;
        case 'maxLength':
          return `${field} must be no more than ${error.params?.limit} characters`;
        case 'pattern':
          return `${field} contains invalid characters`;
        case 'minItems':
          return `${field} must have at least ${error.params?.limit} items`;
        case 'maxItems':
          return `${field} must have no more than ${error.params?.limit} items`;
        case 'minimum':
          return `${field} must be at least ${error.params?.limit}`;
        case 'maximum':
          return `${field} must be no more than ${error.params?.limit}`;
        default:
          return `${field}: ${message}`;
      }
    });

    return {
      valid: false,
      errors: validateWorkflow.errors,
      formattedErrors
    };
  }

  return { valid: true };
}

/**
 * Validate task order and dependencies
 */
export function validateTaskDependencies(workflow: WorkflowCreate): ValidationResult {
  const errors: string[] = [];
  const taskNames = workflow.tasks.map(task => task.name);
  
  // Check for duplicate task names
  const duplicateNames = taskNames.filter((name, index) => taskNames.indexOf(name) !== index);
  if (duplicateNames.length > 0) {
    errors.push(`Duplicate task names found: ${duplicateNames.join(', ')}`);
  }
  
  // For now, we don't check dependencies as WorkflowCreate tasks don't have them
  // Dependencies will be resolved during workflow execution based on order_index
  
  return {
    valid: errors.length === 0,
    formattedErrors: errors
  };
}

/**
 * Comprehensive workflow validation
 */
export function validateCompleteWorkflow(workflow: WorkflowCreate): ValidationResult {
  // Schema validation
  const schemaResult = validateWorkflowData(workflow);
  if (!schemaResult.valid) {
    return schemaResult;
  }
  
  // Dependencies validation
  const depsResult = validateTaskDependencies(workflow);
  if (!depsResult.valid) {
    return depsResult;
  }
  
  return { valid: true };
}

/**
 * Sanitize workflow data before submission
 */
export function sanitizeWorkflowData(workflow: WorkflowCreate): WorkflowCreate {
  return {
    ...workflow,
    name: workflow.name.trim(),
    author: workflow.author.trim(),
    tasks: workflow.tasks.map((task) => {
      // Create clean task object without spreading all properties
      const cleanTask: any = {
        name: task.name.trim(),
        service_parameters: task.service_parameters || {}
      };
      
      // Only include service_id if it's not null/undefined
      if (task.service_id != null) {
        cleanTask.service_id = task.service_id;
      }
      
      return cleanTask;
    })
  };
}