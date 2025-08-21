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
  const warnings: string[] = [];
  
  // Check for empty task names
  const emptyNames = workflow.tasks.filter(task => !task.name.trim());
  if (emptyNames.length > 0) {
    errors.push(`Tasks must have non-empty names`);
  }
  
  // Check for duplicate task names - but only as a warning, not an error
  // Allow duplicate task names since they can have different services or parameters
  const taskNames = workflow.tasks.map(task => task.name);
  const duplicateNames = taskNames.filter((name, index) => taskNames.indexOf(name) !== index);
  const uniqueDuplicates = [...new Set(duplicateNames)];
  
  if (uniqueDuplicates.length > 0) {
    warnings.push(`Note: You have multiple tasks with the same name (${uniqueDuplicates.join(', ')}). This is allowed, but consider adding numbers or descriptions to distinguish them for clarity.`);
  }
  
  // Allow multiple tasks with same name and same service - this is valid
  // Users might want to run the same analysis multiple times with different parameters
  // or at different stages of the workflow
  
  return {
    valid: errors.length === 0,
    formattedErrors: errors.length > 0 ? errors : (warnings.length > 0 ? warnings : undefined)
  };
}

/**
 * Validate service assignments and instrument usage
 */
export function validateServiceAssignments(workflow: WorkflowCreate): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  workflow.tasks.forEach((task, index) => {
    // Check if task has a service assignment
    if (!task.service_id && !task.service_parameters) {
      warnings.push(`Task "${task.name}" has no service or instrument assigned`);
    }
    
    // Check for invalid service IDs
    if (task.service_id && (task.service_id < 1 || !Number.isInteger(task.service_id))) {
      errors.push(`Task "${task.name}" has invalid service ID: ${task.service_id}`);
    }
  });
  
  // Note: Multiple tasks can use the same service/instrument - this is allowed
  // Services and instruments can be reused across different tasks in a workflow
  
  return {
    valid: errors.length === 0,
    formattedErrors: [...errors, ...warnings.map(w => `Warning: ${w}`)]
  };
}

/**
 * Comprehensive workflow validation
 */
export function validateCompleteWorkflow(workflow: WorkflowCreate): ValidationResult {
  const allErrors: string[] = [];
  
  // Schema validation
  const schemaResult = validateWorkflowData(workflow);
  if (!schemaResult.valid) {
    return schemaResult;
  }
  
  // Dependencies validation
  const depsResult = validateTaskDependencies(workflow);
  if (!depsResult.valid && depsResult.formattedErrors) {
    allErrors.push(...depsResult.formattedErrors);
  }
  
  // Service assignments validation  
  const serviceResult = validateServiceAssignments(workflow);
  if (!serviceResult.valid && serviceResult.formattedErrors) {
    allErrors.push(...serviceResult.formattedErrors);
  }
  
  return {
    valid: allErrors.length === 0,
    formattedErrors: allErrors.length > 0 ? allErrors : undefined
  };
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