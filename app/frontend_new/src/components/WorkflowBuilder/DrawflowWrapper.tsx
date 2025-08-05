// src/components/WorkflowBuilder/DrawflowWrapper.tsx

import React, { useEffect, useRef, useCallback, useState } from 'react';
import Drawflow from 'drawflow';
import { Instrument, WorkflowCreationRequest } from '@/types';
import { Play, Pause, Square, Save, Download, Upload, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';

interface DrawflowWrapperProps {
  instruments: Instrument[];
  onWorkflowSave: (workflow: WorkflowCreationRequest) => void;
  onWorkflowLoad?: (data: any) => void;
  initialData?: any;
  readonly?: boolean;
}

interface NodeData {
  task_name: string;
  instrument: string;
  parameters: Record<string, any>;
  estimated_duration?: number;
}

const DrawflowWrapper: React.FC<DrawflowWrapperProps> = ({
  instruments,
  onWorkflowSave,
  onWorkflowLoad,
  initialData,
  readonly = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<Drawflow | null>(null);
  const [workflowName, setWorkflowName] = useState('');
  const [isSimulating, setIsSimulating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Node templates for different lab operations
  const nodeTemplates = {
    sample_prep: {
      name: 'Sample Preparation',
      color: '#3B82F6',
      icon: '🧪',
      inputs: 1,
      outputs: 1,
      defaultParams: { 
        volume: 100, 
        concentration: '1mg/mL',
        temperature: 25,
        mixing_speed: 200
      }
    },
    analysis: {
      name: 'Analysis',
      color: '#10B981',
      icon: '📊',
      inputs: 1,
      outputs: 1,
      defaultParams: { 
        method: 'HPLC', 
        runtime: 30,
        wavelength: 280,
        flow_rate: 1.0
      }
    },
    incubation: {
      name: 'Incubation',
      color: '#F59E0B',
      icon: '🌡️',
      inputs: 1,
      outputs: 1,
      defaultParams: { 
        temperature: 37, 
        duration: 120,
        humidity: 95,
        co2_level: 5
      }
    },
    measurement: {
      name: 'Measurement',
      color: '#EF4444',
      icon: '📏',
      inputs: 1,
      outputs: 1,
      defaultParams: { 
        type: 'absorbance', 
        wavelength: 280,
        read_time: 1,
        number_of_reads: 3
      }
    },
    quality_control: {
      name: 'Quality Control',
      color: '#8B5CF6',
      icon: '✓',
      inputs: 1,
      outputs: 2,
      defaultParams: { 
        standard: 'ISO9001', 
        tolerance: 5,
        acceptance_criteria: 'pass/fail',
        control_type: 'positive'
      }
    },
    data_export: {
      name: 'Data Export',
      color: '#6B7280',
      icon: '💾',
      inputs: 1,
      outputs: 0,
      defaultParams: { 
        format: 'csv', 
        destination: 'LIMS',
        include_metadata: true,
        compression: false
      }
    }
  };

  // Initialize Drawflow
  useEffect(() => {
    if (!containerRef.current || editorRef.current) return;

    const editor = new Drawflow(containerRef.current);
    editor.reroute = true;
    editor.reroute_fix_curvature = true;
    editor.force_first_input = false;
    editor.editor_mode = readonly ? 'view' : 'edit';
    
    editor.start();
    editorRef.current = editor;

    // Load initial data if provided
    if (initialData) {
      editor.import(initialData);
    }

    // Add event listeners
    editor.on('nodeCreated', (id: number) => {
      console.log('Node created:', id);
      validateWorkflow();
    });

    editor.on('nodeRemoved', (id: number) => {
      console.log('Node removed:', id);
      validateWorkflow();
    });

    editor.on('connectionCreated', (info: any) => {
      console.log('Connection created:', info);
      validateWorkflow();
    });

    editor.on('connectionRemoved', (info: any) => {
      console.log('Connection removed:', info);
      validateWorkflow();
    });

    editor.on('nodeDataChanged', (id: number) => {
      console.log('Node data changed:', id);
      validateWorkflow();
    });

    return () => {
      if (editorRef.current) {
        editorRef.current.clear();
        editorRef.current = null;
      }
    };
  }, [initialData, readonly]);

  // Create HTML template for a node
  const createNodeHtml = useCallback((
    type: keyof typeof nodeTemplates,
    data: NodeData,
    nodeId: number
  ) => {
    const template = nodeTemplates[type];
    const availableInstruments = instruments.filter(inst => 
      inst.status === 'available' || inst.id === data.instrument
    );

    return `
      <div class="lab-node lab-node-${type}" style="--node-color: ${template.color}">
        <div class="node-header">
          <span class="node-icon">${template.icon}</span>
          <span class="node-title">${data.task_name || template.name}</span>
        </div>
        <div class="node-content">
          <div class="form-group">
            <label>Task Name:</label>
            <input type="text" df-task_name class="node-input" 
                   value="${data.task_name || template.name}" 
                   placeholder="Enter task name">
          </div>
          <div class="form-group">
            <label>Instrument:</label>
            <select df-instrument class="node-select">
              <option value="">Select instrument...</option>
              ${availableInstruments.map(inst => 
                `<option value="${inst.id}" ${inst.id === data.instrument ? 'selected' : ''}>
                  ${inst.name} (${inst.status})
                </option>`
              ).join('')}
            </select>
          </div>
          <div class="form-group">
            <label>Duration (min):</label>
            <input type="number" df-estimated_duration class="node-input" 
                   value="${data.estimated_duration || 30}" 
                   min="1" max="1440" step="1">
          </div>
          ${Object.entries(template.defaultParams).map(([key, value]) => `
            <div class="form-group">
              <label>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</label>
              <input type="${typeof value === 'number' ? 'number' : 'text'}" 
                     df-${key} class="node-input" 
                     value="${data.parameters?.[key] || value}"
                     ${typeof value === 'number' ? 'step="0.1"' : ''}>
            </div>
          `).join('')}
          <div class="node-status">
            <div class="status-indicator status-pending"></div>
            <span class="status-text">Ready</span>
          </div>
        </div>
      </div>
    `;
  }, [instruments]);

  // Add a new node to the canvas
  const addNode = useCallback((type: keyof typeof nodeTemplates, x?: number, y?: number) => {
    if (!editorRef.current) return;

    const template = nodeTemplates[type];
    const nodeId = editorRef.current.nodeId;
    
    // Get canvas center position if x,y not provided
    const canvasRect = containerRef.current?.getBoundingClientRect();
    const defaultX = x || (canvasRect ? canvasRect.width / 2 - 100 : 100);
    const defaultY = y || (canvasRect ? canvasRect.height / 2 - 50 : 100);
    
    const nodeData: NodeData = {
      task_name: template.name,
      instrument: instruments.find(i => i.status === 'available')?.id || '',
      parameters: { ...template.defaultParams },
      estimated_duration: 30
    };

    const html = createNodeHtml(type, nodeData, nodeId);

    editorRef.current.addNode(
      type,
      template.inputs,
      template.outputs,
      defaultX,
      defaultY,
      `lab-node-${type}`,
      nodeData,
      html
    );

    toast.success(`Added ${template.name} node`);
    validateWorkflow();
  }, [instruments, createNodeHtml, nodeTemplates]);

  // Validate workflow for errors
  const validateWorkflow = useCallback(() => {
    if (!editorRef.current) return false;

    const exportData = editorRef.current.export();
    const nodes = exportData.drawflow.Home.data;
    
    const errors: string[] = [];
    const nodeCount = Object.keys(nodes).length;

    if (nodeCount === 0) {
      setValidationErrors([]);
      return true;
    }

    // Check for disconnected nodes (except single nodes)
    if (nodeCount > 1) {
      Object.values(nodes).forEach((node: any) => {
        const hasInputs = Object.keys(node.inputs).length > 0;
        const hasOutputs = Object.keys(node.outputs).length > 0;
        const hasInputConnections = Object.values(node.inputs).some((input: any) => 
          input.connections.length > 0
        );
        const hasOutputConnections = Object.values(node.outputs).some((output: any) => 
          output.connections.length > 0
        );

        if (hasInputs && !hasInputConnections && hasOutputs && !hasOutputConnections) {
          errors.push(`Node "${node.data.task_name}" is completely disconnected`);
        }
      });
    }

    // Check for missing instruments
    Object.values(nodes).forEach((node: any) => {
      if (!node.data.instrument) {
        errors.push(`Node "${node.data.task_name}" has no instrument assigned`);
      }
    });

    // Check for instrument conflicts (same instrument used simultaneously)
    const instrumentUsage = new Map<string, string[]>();
    Object.values(nodes).forEach((node: any) => {
      const instrument = node.data.instrument;
      if (instrument) {
        if (!instrumentUsage.has(instrument)) {
          instrumentUsage.set(instrument, []);
        }
        instrumentUsage.get(instrument)!.push(node.data.task_name);
      }
    });

    instrumentUsage.forEach((tasks, instrument) => {
      if (tasks.length > 1) {
        // Check if tasks are connected in sequence (allowed) or parallel (conflict)
        const parallelTasks = tasks.filter((task, index, arr) => {
          // This is a simplified check - in a real implementation you'd analyze the graph
          return arr.length > 1;
        });
        if (parallelTasks.length > 1) {
          errors.push(`Instrument "${instrument}" cannot run parallel tasks: ${tasks.join(', ')}`);
        }
      }
    });

    // Check for missing task names
    Object.values(nodes).forEach((node: any) => {
      if (!node.data.task_name || node.data.task_name.trim() === '') {
        errors.push(`Node has empty task name`);
      }
    });

    setValidationErrors(errors);
    return errors.length === 0;
  }, []);

  // Save workflow
  const saveWorkflow = useCallback(() => {
    if (!editorRef.current || !workflowName.trim()) {
      toast.error('Please enter a workflow name');
      return;
    }

    if (!validateWorkflow()) {
      toast.error('Please fix validation errors before saving');
      return;
    }

    const exportData = editorRef.current.export();
    const nodes = exportData.drawflow.Home.data;
    
    if (Object.keys(nodes).length === 0) {
      toast.error('Cannot save empty workflow');
      return;
    }
    
    // Convert Drawflow data to API format
    const tasks = Object.entries(nodes)
      .sort(([, a], [, b]) => (a as any).pos_x - (b as any).pos_x) // Sort by position
      .map(([id, node]: [string, any], index) => ({
        name: node.data.task_name,
        instrument: node.data.instrument,
        parameters: {
          ...node.data.parameters,
          estimated_duration: node.data.estimated_duration
        },
        order_index: index,
      }));

    const totalDuration = tasks.reduce((sum, task) => 
      sum + (task.parameters.estimated_duration || 30), 0
    );

    const workflowData: WorkflowCreationRequest = {
      name: workflowName,
      tasks,
      metadata: {
        description: `Visual workflow with ${tasks.length} tasks`,
        protocol_type: 'custom',
        estimated_duration: totalDuration,
        priority: 'medium',
        lab_location: 'main-lab'
      }
    };

    onWorkflowSave(workflowData);
    toast.success('Workflow saved successfully!');
  }, [workflowName, validateWorkflow, onWorkflowSave]);

  // Export workflow as JSON
  const exportWorkflow = useCallback(() => {
    if (!editorRef.current) return;

    const exportData = editorRef.current.export();
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${workflowName || 'workflow'}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
    toast.success('Workflow exported!');
  }, [workflowName]);

  // Import workflow from JSON
  const importWorkflow = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !editorRef.current) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string);
        editorRef.current!.clear();
        editorRef.current!.import(data);
        if (onWorkflowLoad) {
          onWorkflowLoad(data);
        }
        validateWorkflow();
        toast.success('Workflow imported successfully!');
      } catch (error) {
        toast.error('Invalid workflow file');
      }
    };
    reader.readAsText(file);
    
    // Reset input
    event.target.value = '';
  }, [onWorkflowLoad]);

  // Clear canvas
  const clearCanvas = useCallback(() => {
    if (!editorRef.current) return;
    
    if (window.confirm('Are you sure you want to clear the entire workflow?')) {
      editorRef.current.clear();
      setValidationErrors([]);
      toast.success('Workflow cleared');
    }
  }, []);

  // Simulate workflow execution
  const simulateWorkflow = useCallback(async () => {
    if (!editorRef.current) return;

    if (!validateWorkflow()) {
      toast.error('Fix validation errors before simulation');
      return;
    }

    setIsSimulating(true);
    const exportData = editorRef.current.export();
    const nodes = Object.values(exportData.drawflow.Home.data);
    
    if (nodes.length === 0) {
      toast.error('No nodes to simulate');
      setIsSimulating(false);
      return;
    }
    
    try {
      toast.success('Starting workflow simulation...');
      
      // Reset all nodes
      containerRef.current?.querySelectorAll('.lab-node').forEach(el => {
        el.classList.remove('simulating', 'completed', 'error');
      });

      // Simulate nodes in sequence
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i] as any;
        const nodeElement = containerRef.current?.querySelector(`#node-${node.id}`);
        
        if (nodeElement) {
          // Start simulation
          nodeElement.classList.add('simulating');
          const statusText = nodeElement.querySelector('.status-text');
          const statusIndicator = nodeElement.querySelector('.status-indicator');
          
          if (statusText) statusText.textContent = 'Running...';
          if (statusIndicator) {
            statusIndicator.className = 'status-indicator status-running';
          }

          // Wait for estimated duration (scaled for demo)
          const duration = Math.min(node.data.estimated_duration * 50, 2000); // Max 2 seconds
          await new Promise(resolve => setTimeout(resolve, duration));
          
          // Complete simulation
          nodeElement.classList.remove('simulating');
          nodeElement.classList.add('completed');
          
          if (statusText) statusText.textContent = 'Completed';
          if (statusIndicator) {
            statusIndicator.className = 'status-indicator status-completed';
          }
        }
      }
      
      toast.success('Simulation completed successfully!');
    } catch (error) {
      toast.error('Simulation failed');
      // Mark current node as error
      containerRef.current?.querySelectorAll('.simulating').forEach(el => {
        el.classList.remove('simulating');
        el.classList.add('error');
      });
    } finally {
      setIsSimulating(false);
      
      // Reset after 3 seconds
      setTimeout(() => {
        containerRef.current?.querySelectorAll('.lab-node').forEach(el => {
          el.classList.remove('completed', 'error');
          const statusText = el.querySelector('.status-text');
          const statusIndicator = el.querySelector('.status-indicator');
          if (statusText) statusText.textContent = 'Ready';
          if (statusIndicator) {
            statusIndicator.className = 'status-indicator status-pending';
          }
        });
      }, 3000);
    }
  }, [validateWorkflow]);

  return (
    <div className="workflow-builder h-full flex flex-col">
      {/* Toolbar */}
      <div className="toolbar bg-white border-b border-gray-200 p-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <input
              type="text"
              placeholder="Enter workflow name..."
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={readonly}
            />
            
            {validationErrors.length > 0 && (
              <div className="flex items-center text-red-600">
                <AlertTriangle className="h-4 w-4 mr-1" />
                <span className="text-sm">{validationErrors.length} errors</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {!readonly && (
              <>
                <button
                  onClick={clearCanvas}
                  className="flex items-center space-x-2 px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
                >
                  <Square className="h-4 w-4" />
                  <span>Clear</span>
                </button>
                
                <button
                  onClick={simulateWorkflow}
                  disabled={isSimulating}
                  className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  {isSimulating ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  <span>{isSimulating ? 'Simulating...' : 'Simulate'}</span>
                </button>
                
                <button
                  onClick={saveWorkflow}
                  className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  <Save className="h-4 w-4" />
                  <span>Save</span>
                </button>
              </>
            )}
            
            <button
              onClick={exportWorkflow}
              className="flex items-center space-x-2 px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
            
            {!readonly && (
              <label className="flex items-center space-x-2 px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 cursor-pointer transition-colors">
                <Upload className="h-4 w-4" />
                <span>Import</span>
                <input
                  type="file"
                  accept=".json"
                  onChange={importWorkflow}
                  className="hidden"
                />
              </label>
            )}
          </div>
        </div>
        
        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Validation Errors
                </h3>
                <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Node Palette */}
        {!readonly && (
          <div className="node-palette bg-gray-50 border-r border-gray-200 p-4 w-64 overflow-y-auto flex-shrink-0">
            <h3 className="text-lg font-semibold mb-4">Lab Operations</h3>
            <div className="space-y-2">
              {Object.entries(nodeTemplates).map(([type, template]) => (
                <button
                  key={type}
                  onClick={() => addNode(type as keyof typeof nodeTemplates)}
                  className="w-full flex items-center space-x-3 p-3 bg-white border border-gray-200 rounded-md hover:bg-gray-50 hover:border-gray-300 transition-all duration-200 shadow-sm"
                  style={{ borderLeft: `4px solid ${template.color}` }}
                >
                  <span className="text-2xl">{template.icon}</span>
                  <div className="text-left flex-1">
                    <div className="font-medium text-sm">{template.name}</div>
                    <div className="text-xs text-gray-500">
                      {template.inputs}→{template.outputs}
                    </div>
                  </div>
                </button>
              ))}
            </div>
            
            <div className="mt-6">
              <h4 className="font-medium mb-3 text-sm text-gray-700">Available Instruments</h4>
              <div className="space-y-2">
                {instruments.length > 0 ? instruments.map((instrument) => (
                  <div
                    key={instrument.id}
                    className={`p-2 text-xs rounded-md border ${
                      instrument.status === 'available' 
                        ? 'bg-green-50 text-green-800 border-green-200' 
                        : instrument.status === 'busy'
                        ? 'bg-yellow-50 text-yellow-800 border-yellow-200'
                        : instrument.status === 'maintenance'
                        ? 'bg-orange-50 text-orange-800 border-orange-200'
                        : 'bg-red-50 text-red-800 border-red-200'
                    }`}
                  >
                    <div className="font-medium">{instrument.name}</div>
                    <div className="text-xs opacity-75">{instrument.type} • {instrument.status}</div>
                  </div>
                )) : (
                  <div className="text-xs text-gray-500 p-2">
                    No instruments available
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Canvas */}
        <div className="canvas-container flex-1 relative overflow-hidden">
          <div 
            ref={containerRef} 
            id="drawflow" 
            className="drawflow-canvas h-full w-full"
          />
          
          {/* Canvas overlay for empty state */}
          {!readonly && (
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
              <div className="text-center text-gray-400">
                <div className="text-6xl mb-4">🧪</div>
                <div className="text-lg font-medium">Drag lab operations here</div>
                <div className="text-sm">Start building your workflow</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DrawflowWrapper;