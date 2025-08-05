// TODO: Copy content from artifacts
// src/types/index.ts

export interface Workflow {
  id: number;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  created_at: string;
  updated_at: string;
  tasks: Task[];
  metadata?: {
    description?: string;
    protocol_type?: string;
    estimated_duration?: number;
    priority?: 'low' | 'medium' | 'high' | 'critical';
    lab_location?: string;
  };
}

export interface Task {
  id: number;
  workflow_id: number;
  name: string;
  instrument: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  order_index: number;
  created_at: string;
  updated_at: string;
  results?: Result[];
  parameters?: Record<string, any>;
  estimated_duration?: number;
  actual_duration?: number;
}

export interface Result {
  id: number;
  task_id: number;
  data: Record<string, any>;
  created_at: string;
}

export interface Instrument {
  id: string;
  name: string;
  type: string;
  status: 'available' | 'busy' | 'maintenance' | 'offline';
  location?: string;
  capabilities: string[];
  current_task_id?: number;
  last_calibration?: string;
  next_maintenance?: string;
}

export interface Sample {
  id: string;
  name: string;
  type: string;
  barcode?: string;
  location: string;
  status: 'available' | 'in_use' | 'consumed' | 'quarantined';
  properties?: Record<string, any>;
  created_at: string;
  expiry_date?: string;
}

export interface Protocol {
  id: string;
  name: string;
  description: string;
  version: string;
  steps: ProtocolStep[];
  instruments_required: string[];
  estimated_duration: number;
  sop_document?: string;
}

export interface ProtocolStep {
  id: string;
  name: string;
  description: string;
  instrument_type: string;
  parameters: Record<string, any>;
  order: number;
  estimated_duration: number;
  critical_point?: boolean;
}

// Drawflow specific types
export interface DrawflowNode {
  id: number;
  name: string;
  data: {
    task_name: string;
    instrument: string;
    parameters: Record<string, any>;
    estimated_duration?: number;
  };
  class: string;
  html: string;
  typenode: boolean;
  inputs: Record<string, DrawflowConnection>;
  outputs: Record<string, DrawflowConnection>;
  pos_x: number;
  pos_y: number;
}

export interface DrawflowConnection {
  connections: Array<{
    node: string;
    input?: string;
    output?: string;
  }>;
}

export interface DrawflowData {
  drawflow: {
    Home: {
      data: Record<string, DrawflowNode>;
    };
  };
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface WorkflowCreationRequest {
  name: string;
  tasks: Array<{
    name: string;
    instrument: string;
    parameters?: Record<string, any>;
    order_index: number;
  }>;
  metadata?: Workflow['metadata'];
}

// Node-RED integration types
export interface NodeRedFlow {
  id: string;
  label: string;
  nodes: NodeRedNode[];
  configs: NodeRedConfig[];
}

export interface NodeRedNode {
  id: string;
  type: string;
  name?: string;
  x: number;
  y: number;
  z: string;
  wires: string[][];
  [key: string]: any;
}

export interface NodeRedConfig {
  id: string;
  type: string;
  name: string;
  [key: string]: any;
}

// Laboratory specific types
export interface LabLocation {
  id: string;
  name: string;
  type: 'bench' | 'hood' | 'incubator' | 'storage' | 'waste';
  capacity?: number;
  current_occupancy?: number;
  temperature?: number;
  humidity?: number;
  conditions?: string[];
}

export interface QualityControl {
  id: string;
  workflow_id: number;
  task_id?: number;
  type: 'calibration' | 'blank' | 'standard' | 'duplicate' | 'spike';
  status: 'pending' | 'passed' | 'failed' | 'warning';
  measured_value?: number;
  expected_value?: number;
  tolerance?: number;
  created_at: string;
}

// Form types
export interface WorkflowFormData {
  name: string;
  description?: string;
  protocol_type?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  lab_location?: string;
  estimated_duration?: number;
}

export interface TaskFormData {
  name: string;
  instrument: string;
  parameters: Record<string, any>;
  estimated_duration?: number;
}