// TODO: Copy content from artifacts
// src/pages/WorkflowBuilder.tsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, Play, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import DrawflowWrapper from '@/components/WorkflowBuilder/DrawflowWrapper';
import apiClient from '@/lib/api';
import type { Workflow, Instrument, WorkflowCreationRequest } from '@/types';

const WorkflowBuilder: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = Boolean(id);
  
  const [workflowData, setWorkflowData] = useState<any>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Fetch existing workflow if editing
  const { data: existingWorkflow, isLoading: loadingWorkflow } = useQuery({
    queryKey: ['workflow', id],
    queryFn: () => apiClient.getWorkflow(Number(id!)),
    enabled: isEditing,
  });

  // Fetch instruments for the node palette
  const { data: instruments = [], isLoading: loadingInstruments } = useQuery({
    queryKey: ['instruments'],
    queryFn: () => apiClient.getInstruments(),
  });

  // Create workflow mutation
  const createWorkflowMutation = useMutation({
    mutationFn: (workflow: WorkflowCreationRequest) => apiClient.createWorkflow(workflow),
    onSuccess: (newWorkflow) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      toast.success('Workflow created successfully!');
      navigate(`/workflows/${newWorkflow.id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to create workflow');
    },
  });

  // Update workflow mutation
  const updateWorkflowMutation = useMutation({
    mutationFn: ({ id, workflow }: { id: number; workflow: Partial<Workflow> }) =>
      apiClient.updateWorkflow(id, workflow),
    onSuccess: (updatedWorkflow) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow', id] });
      toast.success('Workflow updated successfully!');
      setHasUnsavedChanges(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to update workflow');
    },
  });

  // Start workflow mutation
  const startWorkflowMutation = useMutation({
    mutationFn: (workflowId: number) => apiClient.startWorkflow(workflowId),
    onSuccess: (startedWorkflow) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow', id] });
      toast.success('Workflow started successfully!');
      navigate(`/workflows/${startedWorkflow.id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to start workflow');
    },
  });

  // Convert existing workflow to Drawflow format
  useEffect(() => {
    if (existingWorkflow && !workflowData) {
      const drawflowData = convertWorkflowToDrawflow(existingWorkflow);
      setWorkflowData(drawflowData);
    }
  }, [existingWorkflow, workflowData]);

  // Convert workflow to Drawflow format
  const convertWorkflowToDrawflow = (workflow: Workflow) => {
    const nodes: Record<string, any> = {};
    
    workflow.tasks.forEach((task, index) => {
      const nodeId = index + 1;
      nodes[nodeId] = {
        id: nodeId,
        name: getNodeTypeFromInstrument(task.instrument),
        data: {
          task_name: task.name,
          instrument: task.instrument,
          parameters: task.parameters || {},
          estimated_duration: task.estimated_duration || 30,
        },
        class: `lab-node-${getNodeTypeFromInstrument(task.instrument)}`,
        html: '',
        typenode: false,
        inputs: index === 0 ? {} : { input_1: { connections: [] } },
        outputs: index === workflow.tasks.length - 1 ? {} : { output_1: { connections: [] } },
        pos_x: 100 + (index * 250),
        pos_y: 200,
      };

      // Connect sequential tasks
      if (index > 0) {
        const prevNodeId = index;
        nodes[prevNodeId].outputs.output_1.connections.push({
          node: nodeId.toString(),
          output: 'input_1',
        });
        nodes[nodeId].inputs.input_1.connections.push({
          node: prevNodeId.toString(),
          input: 'output_1',
        });
      }
    });

    return {
      drawflow: {
        Home: {
          data: nodes,
        },
      },
    };
  };

  // Get node type from instrument
  const getNodeTypeFromInstrument = (instrument: string): string => {
    const instrumentLower = instrument.toLowerCase();
    if (instrumentLower.includes('prep')) return 'sample_prep';
    if (instrumentLower.includes('hplc') || instrumentLower.includes('analysis')) return 'analysis';
    if (instrumentLower.includes('incubator')) return 'incubation';
    if (instrumentLower.includes('measure') || instrumentLower.includes('spec')) return 'measurement';
    if (instrumentLower.includes('qc') || instrumentLower.includes('quality')) return 'quality_control';
    return 'analysis'; // default
  };

  // Handle workflow save
  const handleWorkflowSave = async (workflow: WorkflowCreationRequest) => {
    if (isEditing && existingWorkflow) {
      // Update existing workflow
      updateWorkflowMutation.mutate({
        id: existingWorkflow.id,
        workflow: {
          name: workflow.name,
          metadata: workflow.metadata,
          // Note: In a real implementation, you'd need API endpoints to update tasks
          // For now, we'll just update the workflow metadata
        },
      });
    } else {
      // Create new workflow
      createWorkflowMutation.mutate(workflow);
    }
  };

  // Handle workflow load (for import functionality)
  const handleWorkflowLoad = (data: any) => {
    setWorkflowData(data);
    setHasUnsavedChanges(true);
  };

  // Handle save and start
  const handleSaveAndStart = async (workflow: WorkflowCreationRequest) => {
    if (isEditing && existingWorkflow) {
      // Update and start existing workflow
      try {
        await updateWorkflowMutation.mutateAsync({
          id: existingWorkflow.id,
          workflow: {
            name: workflow.name,
            metadata: workflow.metadata,
          },
        });
        startWorkflowMutation.mutate(existingWorkflow.id);
      } catch (error) {
        // Error is handled by the mutation
      }
    } else {
      // Create and start new workflow
      try {
        const newWorkflow = await createWorkflowMutation.mutateAsync(workflow);
        startWorkflowMutation.mutate(newWorkflow.id);
      } catch (error) {
        // Error is handled by the mutation
      }
    }
  };

  // Prevent navigation with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  if (isEditing && loadingWorkflow) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (loadingInstruments) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/workflows')}
              className="flex items-center text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-5 w-5 mr-2" />
              Back to Workflows
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {isEditing ? 'Edit Workflow' : 'Create New Workflow'}
              </h1>
              {isEditing && existingWorkflow && (
                <p className="text-sm text-gray-500 mt-1">
                  Editing: {existingWorkflow.name}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {hasUnsavedChanges && (
              <div className="flex items-center text-yellow-600">
                <AlertCircle className="h-4 w-4 mr-1" />
                <span className="text-sm">Unsaved changes</span>
              </div>
            )}
            
            <button
              onClick={() => {
                // This will be handled by the DrawflowWrapper component
                // We could add a ref to trigger save from here
              }}
              disabled={createWorkflowMutation.isPending || updateWorkflowMutation.isPending}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              <span>
                {createWorkflowMutation.isPending || updateWorkflowMutation.isPending
                  ? 'Saving...'
                  : 'Save'}
              </span>
            </button>

            <button
              onClick={() => {
                // This will also be handled by the DrawflowWrapper
                // We could add functionality to save and start in one action
              }}
              disabled={
                createWorkflowMutation.isPending ||
                updateWorkflowMutation.isPending ||
                startWorkflowMutation.isPending
              }
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              <Play className="h-4 w-4" />
              <span>
                {startWorkflowMutation.isPending ? 'Starting...' : 'Save & Start'}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Workflow Builder */}
      <div className="flex-1 overflow-hidden">
        <DrawflowWrapper
          instruments={instruments}
          onWorkflowSave={handleWorkflowSave}
          onWorkflowLoad={handleWorkflowLoad}
          initialData={workflowData}
          readonly={false}
        />
      </div>

      {/* Status Bar */}
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-2">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div>
            {instruments.length} instruments available
          </div>
          <div>
            {isEditing ? 'Editing mode' : 'Creation mode'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowBuilder;