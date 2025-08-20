import axios from 'axios';
import { Workflow, WorkflowCreate, Task, Service, TaskTemplate, TaskTemplateCreate } from '../types/workflow';
import { validateCompleteWorkflow, sanitizeWorkflowData } from '../utils/validation';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const workflowAPI = {
  /**
   * Get all workflows - used for polling status updates
   * This follows the backend flow where frontend polls for updates
   */
  async getAll(): Promise<Workflow[]> {
    const response = await api.get('/api/workflows/');
    return response.data;
  },

  /**
   * Get workflow by ID with full task details
   */
  async getById(id: number): Promise<Workflow> {
    const response = await api.get(`/api/workflows/${id}`);
    return response.data;
  },

  /**
   * Create workflow - this triggers the event-driven backend flow:
   * 1. Validates workflow data using JSON schema
   * 2. Sanitizes and sends POST request to backend
   * 3. Backend creates workflow in database
   * 4. Database trigger emits PostgreSQL NOTIFY event
   * 5. Notification listener picks up event and starts workflow
   */
  async create(workflow: WorkflowCreate): Promise<Workflow> {
    // 1. Frontend validation using JSON schema
    const validation = validateCompleteWorkflow(workflow);
    if (!validation.valid) {
      throw new Error(`Validation failed: ${validation.formattedErrors?.join(', ')}`);
    }

    // 2. Sanitize workflow data
    const sanitizedWorkflow = sanitizeWorkflowData(workflow);

    // 3. Send POST request to backend (triggers database event)
    const response = await api.post('/api/workflows/', sanitizedWorkflow);
    
    console.log('[Workflow Created]', response.data);
    console.log('[Event-Driven Flow]', 'Database trigger should start workflow execution');
    
    return response.data;
  },

  /**
   * Update workflow status (used internally by backend)
   */
  async update(id: number, updates: Partial<Workflow>): Promise<Workflow> {
    const response = await api.put(`/api/workflows/${id}`, updates);
    return response.data;
  },

  /**
   * Delete workflow
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/api/workflows/${id}`);
  },

  /**
   * Pause workflow execution
   */
  async pause(id: number): Promise<{ message: string; status: string }> {
    const response = await api.post(`/api/workflows/${id}/pause`);
    return response.data;
  },

  /**
   * Stop workflow execution
   */
  async stop(id: number): Promise<{ message: string; status: string }> {
    const response = await api.post(`/api/workflows/${id}/stop`);
    return response.data;
  },

  /**
   * Resume paused workflow
   */
  async resume(id: number): Promise<{ message: string; status: string }> {
    const response = await api.post(`/api/workflows/${id}/resume`);
    return response.data;
  },

  /**
   * Get workflow execution status for monitoring
   * This is used for polling-based status updates as per the architecture
   */
  async getExecutionStatus(id: number): Promise<{
    workflow: Workflow;
    currentTask?: Task;
    completedTasks: Task[];
    pendingTasks: Task[];
    progress: number;
  }> {
    const workflow = await this.getById(id);
    const tasks = workflow.tasks.sort((a, b) => a.order_index - b.order_index);
    
    const completedTasks = tasks.filter(t => t.status === 'completed');
    const runningTasks = tasks.filter(t => t.status === 'running');
    const pendingTasks = tasks.filter(t => t.status === 'pending');
    
    const progress = tasks.length > 0 ? (completedTasks.length / tasks.length) * 100 : 0;
    
    return {
      workflow,
      currentTask: runningTasks[0],
      completedTasks,
      pendingTasks,
      progress
    };
  }
};

export const taskAPI = {
  async getById(id: number): Promise<Task> {
    const response = await api.get(`/api/tasks/${id}`);
    return response.data;
  },

  async update(id: number, updates: Partial<Task>): Promise<Task> {
    const response = await api.put(`/api/tasks/${id}`, updates);
    return response.data;
  },
};

export const serviceAPI = {
  async getAll(): Promise<Service[]> {
    const response = await api.get('/api/services/');
    return response.data;
  },

  async getById(id: number): Promise<Service> {
    const response = await api.get(`/api/services/${id}`);
    return response.data;
  },

  async create(service: Omit<Service, 'id'>): Promise<Service> {
    const response = await api.post('/api/services/', service);
    return response.data;
  },

  async update(id: number, updates: Partial<Service>): Promise<Service> {
    const response = await api.put(`/api/services/${id}`, updates);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/services/${id}`);
  },
};

export const taskTemplateAPI = {
  async getAll(): Promise<TaskTemplate[]> {
    const response = await api.get('/api/task-templates/');
    return response.data;
  },

  async getById(id: number): Promise<TaskTemplate> {
    const response = await api.get(`/api/task-templates/${id}`);
    return response.data;
  },

  async create(template: TaskTemplateCreate): Promise<TaskTemplate> {
    const response = await api.post('/api/task-templates/', template);
    return response.data;
  },

  async update(id: number, updates: Partial<TaskTemplate>): Promise<TaskTemplate> {
    const response = await api.put(`/api/task-templates/${id}`, updates);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/task-templates/${id}`);
  },
};

export const aiAPI = {
  async generateWorkflow(prompt: string): Promise<WorkflowCreate> {
    const response = await api.post('/api/ai/generate-workflow', { prompt });
    return response.data;
  },
};

// New Instrument Management API
export const instrumentManagementAPI = {
  // Instruments
  async getAllInstruments(): Promise<any[]> {
    const response = await api.get('/api/instrument-management/instruments');
    return response.data;
  },

  async getInstrument(id: string): Promise<any> {
    const response = await api.get(`/api/instrument-management/instruments/${id}`);
    return response.data;
  },

  async createInstrument(instrument: any): Promise<any> {
    const response = await api.post('/api/instrument-management/instruments', instrument);
    return response.data;
  },

  async updateInstrument(id: string, instrument: any): Promise<any> {
    const response = await api.put(`/api/instrument-management/instruments/${id}`, instrument);
    return response.data;
  },

  async deleteInstrument(id: string): Promise<any> {
    const response = await api.delete(`/api/instrument-management/instruments/${id}`);
    return response.data;
  },

  // Tasks
  async getAllTasks(): Promise<any[]> {
    const response = await api.get('/api/instrument-management/tasks');
    return response.data;
  },

  async getTask(id: string): Promise<any> {
    const response = await api.get(`/api/instrument-management/tasks/${id}`);
    return response.data;
  },

  async createTask(task: any): Promise<any> {
    const response = await api.post('/api/instrument-management/tasks', task);
    return response.data;
  },

  async updateTask(id: string, task: any): Promise<any> {
    const response = await api.put(`/api/instrument-management/tasks/${id}`, task);
    return response.data;
  },

  async deleteTask(id: string): Promise<any> {
    const response = await api.delete(`/api/instrument-management/tasks/${id}`);
    return response.data;
  },

  // Node palette data
  async getNodePaletteData(): Promise<{ instruments: any[]; tasks: any[] }> {
    const response = await api.get('/api/instrument-management/node-palette');
    return response.data;
  },

  // Sync to database
  async syncToDatabase(): Promise<any> {
    const response = await api.post('/api/instrument-management/sync-to-database');
    return response.data;
  }
};

export default api;