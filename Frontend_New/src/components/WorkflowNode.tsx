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
  MenuItem
} from '@mui/material';
import { Settings, PlayArrow, CheckCircle, Error } from '@mui/icons-material';
import { NodeData } from '../types/workflow';

const statusColors = {
  pending: '#ff9800',
  running: '#2196f3',
  completed: '#4caf50',
  failed: '#f44336',
  paused: '#ff9800',
  stopped: '#f44336',
};

const statusIcons = {
  pending: <Settings fontSize="small" />,
  running: <PlayArrow fontSize="small" />,
  completed: <CheckCircle fontSize="small" />,
  failed: <Error fontSize="small" />,
  paused: <Settings fontSize="small" />,
  stopped: <Error fontSize="small" />,
};

function WorkflowNode({ data, selected }: NodeProps<NodeData>) {
  const [configOpen, setConfigOpen] = useState(false);
  const [localData, setLocalData] = useState(data);

  const handleConfigClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setConfigOpen(true);
  };

  const handleConfigSave = () => {
    // Update the node data in parent component
    // This would typically update the workflow store
    console.log('Saving node configuration:', localData);
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

  const getParameterFields = () => {
    const parameters = localData.parameters || {};
    
    // Default parameters based on node type
    if (data.type === 'task' && data.serviceId === 1) { // HPLC
      return (
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Column Type"
              value={parameters.column || 'C18'}
              onChange={(e) => handleParameterChange('column', e.target.value)}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Flow Rate"
              value={parameters.flowRate || '1.0 mL/min'}
              onChange={(e) => handleParameterChange('flowRate', e.target.value)}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Temperature"
              value={parameters.temperature || '30°C'}
              onChange={(e) => handleParameterChange('temperature', e.target.value)}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Injection Volume"
              value={parameters.injectionVolume || '10µL'}
              onChange={(e) => handleParameterChange('injectionVolume', e.target.value)}
              fullWidth
            />
          </Grid>
        </Grid>
      );
    } else if (data.type === 'task' && data.serviceId === 3) { // Liquid Handler
      return (
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Tip Type</InputLabel>
              <Select
                value={parameters.tipType || '1000µL'}
                onChange={(e) => handleParameterChange('tipType', e.target.value)}
              >
                <MenuItem value="200µL">200µL</MenuItem>
                <MenuItem value="1000µL">1000µL</MenuItem>
                <MenuItem value="5000µL">5000µL</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Aspiration Speed</InputLabel>
              <Select
                value={parameters.aspirationSpeed || 'medium'}
                onChange={(e) => handleParameterChange('aspirationSpeed', e.target.value)}
              >
                <MenuItem value="slow">Slow</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="fast">Fast</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="Volume"
              value={parameters.volume || '100µL'}
              onChange={(e) => handleParameterChange('volume', e.target.value)}
              fullWidth
            />
          </Grid>
        </Grid>
      );
    } else {
      // Generic parameter editor
      return (
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              label="Task Name"
              value={localData.label}
              onChange={(e) => setLocalData(prev => ({ ...prev, label: e.target.value }))}
              fullWidth
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
        <IconButton size="small" onClick={handleConfigClick}>
          <Settings fontSize="small" />
        </IconButton>
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