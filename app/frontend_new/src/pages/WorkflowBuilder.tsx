import React, { useCallback, useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  Box,
  Paper,
  Toolbar,
  Button,
  TextField,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  Save,
  PlayArrow,
  AutoAwesome,
} from '@mui/icons-material';

import WorkflowNode from '../components/WorkflowNode';
import NodePalette from '../components/NodePalette';
import AIWorkflowGenerator from '../components/AIWorkflowGenerator';
import { useWorkflowStore } from '../store/workflowStore';
import { workflowAPI } from '../services/api';
import { WorkflowCreate, Workflow } from '../types/workflow';

const nodeTypes = {
  workflowNode: WorkflowNode,
};

let nodeId = 0;
const getNodeId = () => `node_${nodeId++}`;

export default function WorkflowBuilder() {
  const { id } = useParams();
  const navigate = useNavigate();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [author, setAuthor] = useState('Lab User');
  const [showAIDialog, setShowAIDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  
  const { currentWorkflow, setCurrentWorkflow, setLoading } = useWorkflowStore();

  // Load existing workflow if editing
  useEffect(() => {
    if (id) {
      loadWorkflow(parseInt(id));
    }
  }, [id]);

  const loadWorkflow = async (workflowId: number) => {
    try {
      setLoading(true);
      const workflow = await workflowAPI.getById(workflowId);
      setCurrentWorkflow(workflow);
      setWorkflowName(workflow.name);
      setAuthor(workflow.author);
      
      // Convert workflow tasks to flow nodes
      const flowNodes: Node[] = workflow.tasks.map((task, index) => ({
        id: task.id.toString(),
        type: 'workflowNode',
        position: { x: 100 + (index % 4) * 250, y: 100 + Math.floor(index / 4) * 150 },
        data: {
          id: task.id.toString(),
          label: task.name,
          type: 'task',
          serviceId: task.service_id,
          parameters: task.service_parameters,
          status: task.status,
        },
      }));
      
      // Create edges based on task order
      const flowEdges: Edge[] = workflow.tasks
        .slice(0, -1)
        .map((task, index) => ({
          id: `edge-${task.id}-${workflow.tasks[index + 1].id}`,
          source: task.id.toString(),
          target: workflow.tasks[index + 1].id.toString(),
          type: 'smoothstep',
        }));
      
      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (error) {
      showSnackbar('Failed to load workflow', 'error');
    } finally {
      setLoading(false);
    }
  };

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      const nodeData = JSON.parse(event.dataTransfer.getData('application/json') || '{}');

      if (typeof type === 'undefined' || !type || !reactFlowInstance) {
        return;
      }

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      // Map instrument IDs to database service IDs for backwards compatibility
      const instrumentToServiceMapping: Record<string, number> = {
        'sample-prep-01': 1,
        'hplc-system-01': 2,
        'gcms-system-01': 6,
        'liquid-handler-01': 7,
      };

      let serviceId: number | undefined = undefined;
      
      if (nodeData.type === 'instrument' && nodeData.sourceData?.id) {
        serviceId = instrumentToServiceMapping[nodeData.sourceData.id];
        console.log(`Mapped instrument ${nodeData.sourceData.id} to service_id ${serviceId}`);
      }

      const newNode: Node = {
        id: getNodeId(),
        type: 'workflowNode',
        position,
        data: {
          id: getNodeId(),
          label: nodeData.label || 'New Node',
          type: nodeData.type || 'task',
          category: nodeData.category,
          description: nodeData.description,
          parameters: nodeData.defaultParameters,
          serviceId: serviceId,
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  const handleDragStart = (event: React.DragEvent, nodeTemplate: any) => {
    event.dataTransfer.setData('application/reactflow', 'workflowNode');
    event.dataTransfer.setData('application/json', JSON.stringify(nodeTemplate));
    event.dataTransfer.effectAllowed = 'move';
  };

  const saveWorkflow = async () => {
    try {
      setLoading(true);
      
      // Validate basic requirements
      if (!workflowName.trim()) {
        showSnackbar('Workflow name is required', 'error');
        return;
      }
      
      if (!author.trim()) {
        showSnackbar('Author name is required', 'error');
        return;
      }
      
      if (nodes.length === 0) {
        showSnackbar('At least one task is required', 'error');
        return;
      }
      
      const workflowData: WorkflowCreate = {
        name: workflowName.trim(),
        author: author.trim(),
        tasks: nodes.map((node, index) => {
          const task: any = {
            name: node.data.label.trim(),
            service_parameters: node.data.parameters || {}
          };
          
          // Only include service_id if it's a valid number (not null/undefined)
          if (typeof node.data.serviceId === 'number' && node.data.serviceId > 0) {
            task.service_id = node.data.serviceId;
          }
          
          return task;
        }),
      };

      console.log('Saving workflow with data:', JSON.stringify(workflowData, null, 2));

      if (id) {
        // Update existing workflow
        const updated = await workflowAPI.update(parseInt(id), workflowData as Partial<Workflow>);
        setCurrentWorkflow(updated);
      } else {
        // Create new workflow
        const created = await workflowAPI.create(workflowData);
        setCurrentWorkflow(created);
        navigate(`/builder/${created.id}`);
      }
      
      showSnackbar('Workflow saved successfully', 'success');
    } catch (error: any) {
      console.error('Workflow save error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to save workflow';
      showSnackbar(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const executeWorkflow = async () => {
    if (!currentWorkflow) {
      showSnackbar('Please save the workflow first', 'error');
      return;
    }

    try {
      setLoading(true);
      // Use the proper execution endpoint
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/workflows/${currentWorkflow.id}/execute-celery`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to start workflow execution');
      }

      const result = await response.json();
      showSnackbar(`Workflow execution started: ${result.message}`, 'success');
      navigate(`/monitor/${currentWorkflow.id}`);
    } catch (error) {
      showSnackbar('Failed to start workflow execution', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAIWorkflowGenerated = (workflow: WorkflowCreate) => {
    setWorkflowName(workflow.name);
    setAuthor(workflow.author);
    
    // Convert AI-generated tasks to flow nodes
    const flowNodes: Node[] = workflow.tasks.map((task, index) => ({
      id: getNodeId(),
      type: 'workflowNode',
      position: { x: 100 + (index % 4) * 250, y: 100 + Math.floor(index / 4) * 150 },
      data: {
        id: getNodeId(),
        label: task.name,
        type: 'task',
        serviceId: task.service_id,
        parameters: task.service_parameters,
      },
    }));
    
    // Create sequential edges
    const flowEdges: Edge[] = flowNodes
      .slice(0, -1)
      .map((node, index) => ({
        id: `edge-${node.id}-${flowNodes[index + 1].id}`,
        source: node.id,
        target: flowNodes[index + 1].id,
        type: 'smoothstep',
      }));
    
    setNodes(flowNodes);
    setEdges(flowEdges);
    showSnackbar('AI workflow generated successfully', 'success');
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const closeSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <ReactFlowProvider>
      <Box className="workflow-builder">
        {/* Sidebar */}
        <Paper className="sidebar" elevation={2}>
          <NodePalette onDragStart={handleDragStart} />
        </Paper>

        {/* Main Content */}
        <Box className="main-content">
          {/* Toolbar */}
          <Paper elevation={1} sx={{ borderRadius: 0 }}>
            <Toolbar>
              <TextField
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                variant="outlined"
                size="small"
                sx={{ mr: 2, minWidth: 200 }}
                placeholder="Workflow Name"
              />
              <TextField
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                variant="outlined"
                size="small"
                sx={{ mr: 2, minWidth: 150 }}
                placeholder="Author"
              />
              
              <Box sx={{ flexGrow: 1 }} />
              
              <Button
                startIcon={<AutoAwesome />}
                onClick={() => setShowAIDialog(true)}
                sx={{ mr: 1 }}
              >
                AI Generate
              </Button>
              <Button
                startIcon={<Save />}
                onClick={saveWorkflow}
                variant="outlined"
                sx={{ mr: 1 }}
              >
                Save
              </Button>
              <Button
                startIcon={<PlayArrow />}
                onClick={executeWorkflow}
                variant="contained"
                disabled={!currentWorkflow}
              >
                Execute
              </Button>
            </Toolbar>
          </Paper>

          {/* React Flow */}
          <Box ref={reactFlowWrapper} sx={{ height: 'calc(100vh - 128px)' }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onInit={setReactFlowInstance}
              onDrop={onDrop}
              onDragOver={onDragOver}
              nodeTypes={nodeTypes}
              fitView
            >
              <Controls />
              <MiniMap />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
            </ReactFlow>
          </Box>
        </Box>

        {/* AI Dialog */}
        <AIWorkflowGenerator
          open={showAIDialog}
          onClose={() => setShowAIDialog(false)}
          onWorkflowGenerated={handleAIWorkflowGenerated}
        />

        {/* Snackbar */}
        <Snackbar 
          open={snackbar.open} 
          autoHideDuration={6000} 
          onClose={closeSnackbar}
        >
          <Alert 
            onClose={closeSnackbar} 
            severity={snackbar.severity}
            variant="filled"
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </ReactFlowProvider>
  );
}