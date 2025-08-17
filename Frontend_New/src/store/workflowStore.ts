import { create } from 'zustand';
import { Workflow, Task, Service, FlowNode } from '../types/workflow';
import { Edge } from 'reactflow';

interface WorkflowStore {
  // State
  workflows: Workflow[];
  currentWorkflow: Workflow | null;
  services: Service[];
  isLoading: boolean;
  error: string | null;
  
  // Flow builder state
  nodes: FlowNode[];
  edges: Edge[];
  selectedNode: FlowNode | null;
  
  // Actions
  setWorkflows: (workflows: Workflow[]) => void;
  setCurrentWorkflow: (workflow: Workflow | null) => void;
  setServices: (services: Service[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Flow builder actions
  setNodes: (nodes: FlowNode[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (node: FlowNode) => void;
  updateNode: (nodeId: string, updates: Partial<FlowNode>) => void;
  removeNode: (nodeId: string) => void;
  setSelectedNode: (node: FlowNode | null) => void;
  
  // Workflow actions
  updateWorkflowStatus: (workflowId: number, status: 'pending' | 'running' | 'completed' | 'failed') => void;
  updateTaskStatus: (taskId: number, status: 'pending' | 'running' | 'completed' | 'failed') => void;
  
  // Reset
  reset: () => void;
}

export const useWorkflowStore = create<WorkflowStore>((set, get) => ({
  // Initial state
  workflows: [],
  currentWorkflow: null,
  services: [],
  isLoading: false,
  error: null,
  nodes: [],
  edges: [],
  selectedNode: null,
  
  // Actions
  setWorkflows: (workflows) => set({ workflows }),
  setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),
  setServices: (services) => set({ services }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  
  // Flow builder actions
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  
  addNode: (node) => {
    const { nodes } = get();
    set({ nodes: [...nodes, node] });
  },
  
  updateNode: (nodeId, updates) => {
    const { nodes } = get();
    set({
      nodes: nodes.map(node => 
        node.id === nodeId ? { ...node, ...updates } : node
      )
    });
  },
  
  removeNode: (nodeId) => {
    const { nodes, edges } = get();
    set({
      nodes: nodes.filter(node => node.id !== nodeId),
      edges: edges.filter(edge => edge.source !== nodeId && edge.target !== nodeId)
    });
  },
  
  setSelectedNode: (node) => set({ selectedNode: node }),
  
  // Workflow actions
  updateWorkflowStatus: (workflowId, status) => {
    const { workflows, currentWorkflow } = get();
    
    set({
      workflows: workflows.map(w => 
        w.id === workflowId ? { ...w, status } : w
      ),
      currentWorkflow: currentWorkflow?.id === workflowId 
        ? { ...currentWorkflow, status } 
        : currentWorkflow
    });
  },
  
  updateTaskStatus: (taskId, status) => {
    const { workflows, currentWorkflow } = get();
    
    const updateTasks = (tasks: Task[]) => 
      tasks.map(task => 
        task.id === taskId ? { ...task, status } : task
      );
    
    set({
      workflows: workflows.map(w => ({
        ...w,
        tasks: updateTasks(w.tasks)
      })),
      currentWorkflow: currentWorkflow ? {
        ...currentWorkflow,
        tasks: updateTasks(currentWorkflow.tasks)
      } : null
    });
  },
  
  reset: () => set({
    workflows: [],
    currentWorkflow: null,
    services: [],
    isLoading: false,
    error: null,
    nodes: [],
    edges: [],
    selectedNode: null,
  }),
}));