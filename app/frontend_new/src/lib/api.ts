// TODO: Copy content from artifacts
// src/lib/api.ts

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';
import type { 
  Workflow, 
  Task, 
  Result, 
  Instrument, 
  Sample, 
  Protocol,
  ApiResponse,
  WorkflowCreationRequest 
} from '@/types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        } else if (error.response?.status >= 500) {
          toast.error('Server error occurred. Please try again.');
        }
        return Promise.reject(error);
      }
    );
  }

  // Workflow endpoints
  async getWorkflows(): Promise<Workflow[]> {
    const response: AxiosResponse<Workflow[]> = await this.client.get('/workflows');
    return response.data;
  }

  async getWorkflow(id: number): Promise<Workflow> {
    const response: AxiosResponse<Workflow> = await this.client.get(`/workflows/${id}`);
    return response.data;
  }

  async createWorkflow(workflow: WorkflowCreationRequest): Promise<Workflow> {
    const response: AxiosResponse<Workflow> = await this.client.post('/workflows', workflow);
    return response.data;
  }

  async updateWorkflow(id: number, workflow: Partial<Workflow>): Promise<Workflow> {
    const response: AxiosResponse<Workflow> = await this.client.put(`/workflows/${id}`, workflow);
    return response.data;
  }

  async deleteWorkflow(id: number): Promise<void> {
    await this.client.delete(`/workflows/${id}`);
  }

  async startWorkflow(id: number): Promise<Workflow> {
    const response: AxiosResponse<Workflow> = await this.client.post(`/workflows/${id}/start`);
    return response.data;
  }

  async pauseWorkflow(id: number): Promise<Workflow> {
    const response: AxiosResponse<Workflow> = await this.client.post(`/workflows/${id}/pause`);
    return response.data;
  }

  async resumeWorkflow(id: number): Promise<Workflow> {
    const response: AxiosResponse<Workflow> = await this.client.post(`/workflows/${id}/resume`);
    return response.data;
  }

  async stopWorkflow(id: number): Promise<Workflow> {
    const response: AxiosResponse<Workflow> = await this.client.post(`/workflows/${id}/stop`);
    return response.data;
  }

  // Task endpoints
  async getTasks(workflowId?: number): Promise<Task[]> {
    const url = workflowId ? `/tasks?workflow_id=${workflowId}` : '/tasks';
    const response: AxiosResponse<Task[]> = await this.client.get(url);
    return response.data;
  }

  async getTask(id: number): Promise<Task> {
    const response: AxiosResponse<Task> = await this.client.get(`/tasks/${id}`);
    return response.data;
  }

  async updateTask(id: number, task: Partial<Task>): Promise<Task> {
    const response: AxiosResponse<Task> = await this.client.put(`/tasks/${id}`, task);
    return response.data;
  }

  async deleteTask(id: number): Promise<void> {
    await this.client.delete(`/tasks/${id}`);
  }

  async retryTask(id: number): Promise<Task> {
    const response: AxiosResponse<Task> = await this.client.post(`/tasks/${id}/retry`);
    return response.data;
  }

  // Results endpoints
  async getResults(taskId: number): Promise<Result[]> {
    const response: AxiosResponse<Result[]> = await this.client.get(`/tasks/${taskId}/results`);
    return response.data;
  }

  async downloadResults(taskId: number, format: 'csv' | 'json' | 'xlsx' = 'csv'): Promise<Blob> {
    const response: AxiosResponse<Blob> = await this.client.get(
      `/tasks/${taskId}/results/download?format=${format}`,
      { responseType: 'blob' }
    );
    return response.data;
  }

  // Instrument endpoints
  async getInstruments(): Promise<Instrument[]> {
    const response: AxiosResponse<Instrument[]> = await this.client.get('/instruments');
    return response.data;
  }

  async getInstrument(id: string): Promise<Instrument> {
    const response: AxiosResponse<Instrument> = await this.client.get(`/instruments/${id}`);
    return response.data;
  }

  async updateInstrument(id: string, instrument: Partial<Instrument>): Promise<Instrument> {
    const response: AxiosResponse<Instrument> = await this.client.put(`/instruments/${id}`, instrument);
    return response.data;
  }

  async calibrateInstrument(id: string): Promise<Instrument> {
    const response: AxiosResponse<Instrument> = await this.client.post(`/instruments/${id}/calibrate`);
    return response.data;
  }

  async maintenanceInstrument(id: string): Promise<Instrument> {
    const response: AxiosResponse<Instrument> = await this.client.post(`/instruments/${id}/maintenance`);
    return response.data;
  }

  // Sample endpoints
  async getSamples(): Promise<Sample[]> {
    const response: AxiosResponse<Sample[]> = await this.client.get('/samples');
    return response.data;
  }

  async getSample(id: string): Promise<Sample> {
    const response: AxiosResponse<Sample> = await this.client.get(`/samples/${id}`);
    return response.data;
  }

  async createSample(sample: Omit<Sample, 'id' | 'created_at'>): Promise<Sample> {
    const response: AxiosResponse<Sample> = await this.client.post('/samples', sample);
    return response.data;
  }

  async updateSample(id: string, sample: Partial<Sample>): Promise<Sample> {
    const response: AxiosResponse<Sample> = await this.client.put(`/samples/${id}`, sample);
    return response.data;
  }

  async deleteSample(id: string): Promise<void> {
    await this.client.delete(`/samples/${id}`);
  }

  // Protocol endpoints
  async getProtocols(): Promise<Protocol[]> {
    const response: AxiosResponse<Protocol[]> = await this.client.get('/protocols');
    return response.data;
  }

  async getProtocol(id: string): Promise<Protocol> {
    const response: AxiosResponse<Protocol> = await this.client.get(`/protocols/${id}`);
    return response.data;
  }

  async createProtocol(protocol: Omit<Protocol, 'id'>): Promise<Protocol> {
    const response: AxiosResponse<Protocol> = await this.client.post('/protocols', protocol);
    return response.data;
  }

  async updateProtocol(id: string, protocol: Partial<Protocol>): Promise<Protocol> {
    const response: AxiosResponse<Protocol> = await this.client.put(`/protocols/${id}`, protocol);
    return response.data;
  }

  async deleteProtocol(id: string): Promise<void> {
    await this.client.delete(`/protocols/${id}`);
  }

  // Node-RED integration endpoints
  async deployNodeRedFlow(workflowId: number): Promise<{ flow_id: string }> {
    const response: AxiosResponse<{ flow_id: string }> = await this.client.post(`/workflows/${workflowId}/deploy-nodered`);
    return response.data;
  }

  async getNodeRedFlowStatus(flowId: string): Promise<{ status: string, nodes: any[] }> {
    const response: AxiosResponse<{ status: string, nodes: any[] }> = await this.client.get(`/nodered/flows/${flowId}/status`);
    return response.data;
  }

  // Dashboard and analytics endpoints
  async getDashboardStats(): Promise<{
    active_workflows: number;
    completed_today: number;
    instruments_busy: number;
    samples_processed: number;
  }> {
    const response = await this.client.get('/dashboard/stats');
    return response.data;
  }

  async getWorkflowAnalytics(timeRange: '1d' | '7d' | '30d' = '7d'): Promise<{
    completion_times: Array<{ date: string; average_duration: number }>;
    success_rate: Array<{ date: string; success_rate: number }>;
    instrument_utilization: Array<{ instrument: string; utilization: number }>;
  }> {
    const response = await this.client.get(`/analytics/workflows?range=${timeRange}`);
    return response.data;
  }

  // File upload endpoints
  async uploadFile(file: File, type: 'protocol' | 'sop' | 'result'): Promise<{ file_id: string; url: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    const response: AxiosResponse<{ file_id: string; url: string }> = await this.client.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async downloadFile(fileId: string): Promise<Blob> {
    const response: AxiosResponse<Blob> = await this.client.get(`/files/${fileId}`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;