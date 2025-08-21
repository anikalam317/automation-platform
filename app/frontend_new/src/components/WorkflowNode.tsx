import React, { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { 
  Box, 
  Typography, 
  Chip, 
  IconButton, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  TextField, 
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  Divider
} from '@mui/material';
import { Settings, PlayArrow, CheckCircle, Error, PersonAdd, DoneAll } from '@mui/icons-material';
import { NodeData } from '../types/workflow';

const statusColors = {
  pending: '#ff9800',
  running: '#2196f3',
  completed: '#4caf50',
  failed: '#f44336',
  paused: '#ff9800',
  stopped: '#f44336',
  awaiting_manual_completion: '#9c27b0',
};

const statusIcons = {
  pending: <Settings fontSize="small" />,
  running: <PlayArrow fontSize="small" />,
  completed: <CheckCircle fontSize="small" />,
  failed: <Error fontSize="small" />,
  paused: <Settings fontSize="small" />,
  stopped: <Error fontSize="small" />,
  awaiting_manual_completion: <PersonAdd fontSize="small" />,
};

interface WorkflowNodeProps extends NodeProps<NodeData> {
  onUpdateNode?: (nodeId: string, newData: Partial<NodeData>) => void;
}

function WorkflowNode({ data, selected, id, onUpdateNode }: WorkflowNodeProps) {
  const [configOpen, setConfigOpen] = useState(false);
  const [localData, setLocalData] = useState(data);
  const [manualCompleteOpen, setManualCompleteOpen] = useState(false);
  const [userName, setUserName] = useState('');
  const [completionNotes, setCompletionNotes] = useState('');

  // Debug logging (can be removed in production)
  // React.useEffect(() => {
  //   console.log('WorkflowNode data:', {
  //     label: data.label,
  //     status: data.status,
  //     workflowId: data.workflowId,
  //     taskId: data.taskId,
  //     showManualButton: (data.status === 'pending' || data.status === 'failed' || data.status === 'awaiting_manual_completion')
  //   });
  // }, [data]);

  // Update localData when data prop changes (for external updates)
  React.useEffect(() => {
    setLocalData(data);
  }, [data]);

  const handleConfigClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setConfigOpen(true);
  };

  const handleManualCompleteClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setManualCompleteOpen(true);
  };

  const handleManualComplete = async () => {
    if (!userName.trim()) {
      alert('Please enter your name');
      return;
    }

    try {
      // Get workflow ID from data or context
      const workflowId = data.workflowId; // Assuming workflowId is passed in data
      const taskId = data.taskId || id; // Use taskId if available, otherwise node id
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/workflows/${workflowId}/tasks/${taskId}/complete-manual`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_name: userName.trim(),
          completion_notes: completionNotes.trim() || undefined
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        // Update node status via callback
        if (onUpdateNode && id) {
          onUpdateNode(id, {
            status: 'completed',
            completedBy: userName.trim(),
            completionMethod: 'manual',
            completionTimestamp: new Date().toISOString()
          });
        }
        
        setManualCompleteOpen(false);
        setUserName('');
        setCompletionNotes('');
        
        alert(`Task marked as completed by ${userName}. The next task will start automatically.`);
        
        // Trigger a page refresh after a short delay to show updated workflow status
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        const error = await response.json();
        console.error('Manual completion error:', error);
        alert(`Failed to complete task: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error completing task manually:', error);
      alert(`Network error: Failed to complete task. Please check your connection and try again.`);
    }
  };

  const handleConfigSave = () => {
    // Update the node data in the parent WorkflowBuilder
    if (onUpdateNode && id) {
      onUpdateNode(id, {
        parameters: localData.parameters,
        label: localData.label,
        description: localData.description
      });
    }
    setConfigOpen(false);
  };

  const handleParameterChange = (key: string, value: any) => {
    setLocalData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [key]: value
      }
    }));
  };

  // Helper function to render a single parameter field
  const renderParameterField = (key: string, paramConfig: any, sectionName: string = '') => {
    const parameters = localData.parameters || {};
    let currentValue = parameters[key] ?? paramConfig.default ?? '';
    
    // Initialize materials table with default rows if empty
    if (paramConfig.type === 'table' && key === 'materials_table' && (!currentValue || currentValue.length === 0)) {
      currentValue = [
        { run: 1, material_1: 0.1, material_2: 0.05, material_3: 0.02, material_4: 0, material_5: 0 }
      ];
      // Update the parameters with the default value
      handleParameterChange(key, currentValue);
    }
    
    const fieldProps = {
      fullWidth: true,
      size: "small" as const,
      margin: "dense" as const
    };

    switch (paramConfig.type) {
      case 'string':
        return (
          <Grid item xs={12} sm={6} key={key}>
            <TextField
              label={paramConfig.label || key}
              value={currentValue}
              placeholder={paramConfig.placeholder}
              onChange={(e) => handleParameterChange(key, e.target.value)}
              required={paramConfig.required}
              disabled={paramConfig.readonly}
              {...fieldProps}
            />
          </Grid>
        );

      case 'text':
        return (
          <Grid item xs={12} key={key}>
            <TextField
              label={paramConfig.label || key}
              value={currentValue}
              placeholder={paramConfig.placeholder}
              onChange={(e) => handleParameterChange(key, e.target.value)}
              required={paramConfig.required}
              multiline
              rows={2}
              {...fieldProps}
            />
          </Grid>
        );

      case 'number':
        return (
          <Grid item xs={12} sm={6} key={key}>
            <TextField
              label={paramConfig.label || key}
              type="number"
              value={currentValue}
              onChange={(e) => handleParameterChange(key, parseFloat(e.target.value) || 0)}
              required={paramConfig.required}
              inputProps={{
                min: paramConfig.min,
                max: paramConfig.max,
                step: paramConfig.step
              }}
              {...fieldProps}
            />
          </Grid>
        );

      case 'boolean':
        return (
          <Grid item xs={12} sm={6} key={key}>
            <FormControlLabel
              control={
                <Switch
                  checked={Boolean(currentValue)}
                  onChange={(e) => handleParameterChange(key, e.target.checked)}
                />
              }
              label={paramConfig.label || key}
            />
          </Grid>
        );

      case 'select':
        return (
          <Grid item xs={12} sm={6} key={key}>
            <FormControl {...fieldProps}>
              <InputLabel>{paramConfig.label || key}</InputLabel>
              <Select
                value={currentValue}
                onChange={(e) => handleParameterChange(key, e.target.value)}
                required={paramConfig.required}
              >
                {paramConfig.options?.map((option: string) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        );

      case 'table':
        return (
          <Grid item xs={12} key={key}>
            <Typography variant="subtitle2" gutterBottom>
              {paramConfig.label || key}
            </Typography>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {paramConfig.columns?.map((col: any) => (
                      <TableCell key={col.name}>{col.label}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(currentValue || []).map((row: any, index: number) => (
                    <TableRow key={index}>
                      {paramConfig.columns?.map((col: any) => (
                        <TableCell key={col.name}>
                          {col.type === 'number' ? (
                            <TextField
                              type="number"
                              value={row[col.name] || ''}
                              onChange={(e) => {
                                const newTable = [...(currentValue || [])];
                                newTable[index] = { ...newTable[index], [col.name]: parseFloat(e.target.value) || 0 };
                                handleParameterChange(key, newTable);
                              }}
                              size="small"
                              inputProps={{
                                min: col.min,
                                max: col.max,
                                step: col.step
                              }}
                            />
                          ) : (
                            <TextField
                              value={row[col.name] || ''}
                              onChange={(e) => {
                                const newTable = [...(currentValue || [])];
                                newTable[index] = { ...newTable[index], [col.name]: e.target.value };
                                handleParameterChange(key, newTable);
                              }}
                              size="small"
                              disabled={col.readonly}
                            />
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <Button
                onClick={() => {
                  const newRow = {};
                  paramConfig.columns?.forEach((col: any) => {
                    if (col.auto_increment) {
                      newRow[col.name] = (currentValue || []).length + 1;
                    } else {
                      newRow[col.name] = col.type === 'number' ? 0 : '';
                    }
                  });
                  handleParameterChange(key, [...(currentValue || []), newRow]);
                }}
                size="small"
                sx={{ mt: 1 }}
              >
                Add Row
              </Button>
            </Paper>
          </Grid>
        );

      default:
        return (
          <Grid item xs={12} sm={6} key={key}>
            <TextField
              label={paramConfig.label || key}
              value={currentValue}
              onChange={(e) => handleParameterChange(key, e.target.value)}
              {...fieldProps}
            />
          </Grid>
        );
    }
  };

  const getParameterFields = () => {
    // Get parameter schema from sourceData (from NodePalette)
    const sourceData = data.sourceData;
    
    if (sourceData && sourceData.common_parameters) {
      // New format with common_parameters and specific_parameters
      return (
        <Box>
          {/* Common Parameters Section */}
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Common Parameters
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(sourceData.common_parameters).map(([key, paramConfig]) =>
              renderParameterField(key, paramConfig, 'common')
            )}
          </Grid>

          {/* Specific Parameters Section */}
          {sourceData.specific_parameters && (
            <>
              <Divider sx={{ my: 3 }} />
              <Typography variant="h6" gutterBottom>
                Specific Parameters
              </Typography>
              <Grid container spacing={2}>
                {Object.entries(sourceData.specific_parameters).map(([key, paramConfig]) =>
                  renderParameterField(key, paramConfig, 'specific')
                )}
              </Grid>
            </>
          )}
        </Box>
      );
    } else if (sourceData && sourceData.parameters) {
      // Legacy format with merged parameters
      return (
        <Grid container spacing={2}>
          {Object.entries(sourceData.parameters).map(([key, paramConfig]) =>
            renderParameterField(key, paramConfig)
          )}
        </Grid>
      );
    } else {
      // Fallback to basic fields if no schema available
      return (
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              label="Name"
              value={localData.label}
              onChange={(e) => setLocalData(prev => ({ ...prev, label: e.target.value }))}
              fullWidth
              size="small"
              margin="dense"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="Description"
              value={localData.description || ''}
              onChange={(e) => setLocalData(prev => ({ ...prev, description: e.target.value }))}
              fullWidth
              multiline
              rows={2}
              size="small"
              margin="dense"
            />
          </Grid>
        </Grid>
      );
    }
  };

  return (
    <>
      {/* Configuration Dialog */}
      <Dialog open={configOpen} onClose={() => setConfigOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Configure Task: {data.label}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {getParameterFields()}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigOpen(false)}>Cancel</Button>
          <Button onClick={handleConfigSave} variant="contained">
            Save Configuration
          </Button>
        </DialogActions>
      </Dialog>

      {/* Manual Completion Dialog */}
      <Dialog open={manualCompleteOpen} onClose={() => setManualCompleteOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Mark Task as Completed: {data.label}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              label="Your Name"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              fullWidth
              margin="dense"
              required
              placeholder="Enter your name for audit trail"
            />
            <TextField
              label="Completion Notes (Optional)"
              value={completionNotes}
              onChange={(e) => setCompletionNotes(e.target.value)}
              fullWidth
              multiline
              rows={3}
              margin="dense"
              placeholder="Add any notes about how this task was completed"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setManualCompleteOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleManualComplete} 
            variant="contained" 
            color="success"
            startIcon={<DoneAll />}
          >
            Mark Complete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Node Component */}
      <Box
        sx={{
          background: 'white',
          border: `2px solid ${selected ? '#dc004e' : '#1976d2'}`,
          borderRadius: 2,
          padding: 2,
          minWidth: 200,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          position: 'relative',
        }}
      >
      <Handle 
        type="target" 
        position={Position.Top} 
        style={{ background: '#555' }}
      />
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
        <Typography variant="h6" sx={{ color: '#1976d2', fontWeight: 'bold', fontSize: '0.9rem' }}>
          {data.label}
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton size="small" onClick={handleConfigClick} title="Configure Parameters">
            <Settings fontSize="small" />
          </IconButton>
          {/* Show manual completion button for pending, failed, or awaiting manual completion tasks */}
          {(data.status === 'pending' || data.status === 'failed' || data.status === 'awaiting_manual_completion') && (
            <IconButton 
              size="small" 
              onClick={handleManualCompleteClick}
              title="Mark as Manually Completed"
              sx={{ color: '#4caf50' }}
            >
              <DoneAll fontSize="small" />
            </IconButton>
          )}
        </Box>
      </Box>
      
      <Typography variant="caption" sx={{ color: '#666', textTransform: 'uppercase', display: 'block', mb: 1 }}>
        {data.type}
      </Typography>
      
      {data.description && (
        <Typography variant="body2" sx={{ color: '#666', fontSize: '0.8rem', mb: 1 }}>
          {data.description}
        </Typography>
      )}
      
      {data.status && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            icon={statusIcons[data.status]}
            label={data.status}
            size="small"
            sx={{
              backgroundColor: statusColors[data.status],
              color: 'white',
              fontSize: '0.7rem',
              height: 20,
            }}
          />
        </Box>
      )}
      
      {/* Show completion information for manually completed tasks */}
      {data.status === 'completed' && data.completedBy && (
        <Typography variant="caption" sx={{ color: '#4caf50', display: 'block', mt: 1, fontStyle: 'italic' }}>
          Completed by: {data.completedBy} ({data.completionMethod || 'manual'})
        </Typography>
      )}
      
      {data.category && (
        <Typography variant="caption" sx={{ color: '#888', display: 'block', mt: 1 }}>
          Category: {data.category}
        </Typography>
      )}
      
      <Handle 
        type="source" 
        position={Position.Bottom} 
        style={{ background: '#555' }}
      />
    </Box>
    </>
  );
}

export default memo(WorkflowNode);