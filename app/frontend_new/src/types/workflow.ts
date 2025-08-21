export interface Task {
  id: number;
  name: string;
  workflow_id: number;
  service_id?: number;
  service_parameters?: Record<string, any>;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'awaiting_manual_completion';
  order_index: number;
  executed_at: string;
  results?: Result[];
  manual_completion?: boolean;
  completed_by?: string;
  completion_method?: string;
  completion_timestamp?: string;
  task_type?: string;
}

export interface Result {
  id: number;
  task_id: number;
  data: Record<string, any>;
  created_at: string;
}

export interface Workflow {
  id: number;
  name: string;
  author: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused' | 'stopped';
  workflow_hash?: string;
  created_at: string;
  updated_at: string;
  tasks: Task[];
}

export interface WorkflowCreate {
  name: string;
  author: string;
  tasks: Array<{
    name: string;
    order_index?: number;
    service_id?: number;
    service_parameters?: Record<string, any>;
  }>;
}

export interface Service {
  id: number;
  name: string;
  description: string;
  type: string;
  endpoint: string;
  default_parameters: Record<string, any>;
  enabled: boolean;
}

export interface TaskTemplate {
  id: number;
  name: string;
  description: string;
  category: string;
  type: string;
  required_service_type?: string;
  default_parameters: Record<string, any>;
  estimated_duration: number;
  enabled: boolean;
}

export interface TaskTemplateCreate {
  name: string;
  description: string;
  category: string;
  type: string;
  required_service_type?: string;
  default_parameters: Record<string, any>;
  estimated_duration: number;
  enabled: boolean;
}

export interface Instrument extends Service {
  category: 'analytical' | 'preparative' | 'storage' | 'processing';
  capabilities: string[];
}

export interface NodeData {
  id: string;
  label: string;
  type: 'task' | 'instrument' | 'decision' | 'start' | 'end' | 'service';
  serviceId?: number;
  parameters?: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'paused' | 'stopped' | 'awaiting_manual_completion';
  category?: string;
  description?: string;
  sourceData?: any; // Contains the original parameter schema from JSON files
  workflowId?: number;
  taskId?: number;
  completedBy?: string;
  completionMethod?: string;
  completionTimestamp?: string;
}

export interface FlowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: NodeData;
  style?: Record<string, any>;
}