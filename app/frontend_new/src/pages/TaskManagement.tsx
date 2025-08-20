import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Fab,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Autocomplete
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Assignment as TaskIcon,
  Timeline as TimelineIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';

interface TaskDefinition {
  id: string;
  name: string;
  category: string;
  description: string;
  workflow_position: string;
  compatible_instruments: string[];
  parameters: Record<string, any>;
  quality_checks: string[];
  outputs: string[];
  prerequisites: string[];
  estimated_duration_seconds: number;
  success_criteria: Record<string, any>;
  status: string;
  created_by: string;
  created_at?: string;
  updated_at?: string;
}

interface InstrumentDefinition {
  id: string;
  name: string;
  category: string;
}

const TaskManagement: React.FC = () => {
  const [tasks, setTasks] = useState<TaskDefinition[]>([]);
  const [instruments, setInstruments] = useState<InstrumentDefinition[]>([]);
  const [selectedTask, setSelectedTask] = useState<TaskDefinition | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state for creating/editing tasks
  const [formData, setFormData] = useState<Partial<TaskDefinition>>({
    name: '',
    category: 'analytical',
    description: '',
    workflow_position: 'intermediate',
    compatible_instruments: [],
    parameters: {},
    quality_checks: [],
    outputs: [],
    prerequisites: [],
    estimated_duration_seconds: 60,
    success_criteria: {},
    status: 'active'
  });

  const categories = [
    'preparative',
    'analytical',
    'processing',
    'quality-control',
    'data-analysis'
  ];

  const workflowPositions = [
    'initial',
    'intermediate', 
    'analytical',
    'final'
  ];

  useEffect(() => {
    fetchTasks();
    fetchInstruments();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/instrument-management/tasks');
      if (response.ok) {
        const data = await response.json();
        setTasks(data);
      } else {
        throw new Error('Failed to fetch tasks');
      }
    } catch (err) {
      setError('Failed to load tasks');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInstruments = async () => {
    try {
      const response = await fetch('/api/instrument-management/instruments');
      if (response.ok) {
        const data = await response.json();
        setInstruments(data);
      }
    } catch (err) {
      console.error('Failed to load instruments:', err);
    }
  };

  const handleCreateTask = () => {
    setFormData({
      name: '',
      category: 'analytical',
      description: '',
      workflow_position: 'intermediate',
      compatible_instruments: [],
      parameters: {},
      quality_checks: [],
      outputs: [],
      prerequisites: [],
      estimated_duration_seconds: 60,
      success_criteria: {},
      status: 'active'
    });
    setSelectedTask(null);
    setEditDialogOpen(true);
  };

  const handleEditTask = (task: TaskDefinition) => {
    setFormData(task);
    setSelectedTask(task);
    setEditDialogOpen(true);
  };

  const handleSaveTask = async () => {
    try {
      if (!formData.id) {
        // Generate ID from name
        formData.id = formData.name?.toLowerCase().replace(/\\s+/g, '-').replace(/[^a-z0-9-]/g, '') || '';
      }

      const method = selectedTask ? 'PUT' : 'POST';
      const url = selectedTask 
        ? `/api/instrument-management/tasks/${selectedTask.id}`
        : '/api/instrument-management/tasks';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setSuccess(selectedTask ? 'Task updated successfully' : 'Task created successfully');
        setEditDialogOpen(false);
        fetchTasks(); // Refresh list
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save task');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save task');
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
      const response = await fetch(`/api/instrument-management/tasks/${taskId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setSuccess('Task deleted successfully');
        fetchTasks(); // Refresh list
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete task');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete task');
    }
  };

  const addQualityCheck = () => {
    const check = prompt('Enter new quality check:');
    if (check) {
      setFormData({
        ...formData,
        quality_checks: [...(formData.quality_checks || []), check]
      });
    }
  };

  const removeQualityCheck = (index: number) => {
    setFormData({
      ...formData,
      quality_checks: formData.quality_checks?.filter((_, i) => i !== index) || []
    });
  };

  const addOutput = () => {
    const output = prompt('Enter new output:');
    if (output) {
      setFormData({
        ...formData,
        outputs: [...(formData.outputs || []), output]
      });
    }
  };

  const removeOutput = (index: number) => {
    setFormData({
      ...formData,
      outputs: formData.outputs?.filter((_, i) => i !== index) || []
    });
  };

  const addPrerequisite = () => {
    const prereq = prompt('Enter new prerequisite:');
    if (prereq) {
      setFormData({
        ...formData,
        prerequisites: [...(formData.prerequisites || []), prereq]
      });
    }
  };

  const removePrerequisite = (index: number) => {
    setFormData({
      ...formData,
      prerequisites: formData.prerequisites?.filter((_, i) => i !== index) || []
    });
  };

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>Loading tasks...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TaskIcon /> Laboratory Task Management
        </Typography>
        <Fab
          color="primary"
          aria-label="add"
          onClick={handleCreateTask}
        >
          <AddIcon />
        </Fab>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Manage your laboratory tasks. Define new analytical procedures, configure existing ones, and they will 
        automatically appear in the workflow builder node palette.
      </Typography>

      <Grid container spacing={3}>
        {tasks.map((task) => (
          <Grid item xs={12} md={6} lg={4} key={task.id}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" component="h3">
                    {task.name}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    <Chip
                      label={task.category}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                    <Chip
                      label={task.workflow_position}
                      size="small"
                      color="secondary"
                      variant="outlined"
                    />
                  </Box>
                </Box>

                <Typography variant="body2" sx={{ mb: 2 }}>
                  {task.description}
                </Typography>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Compatible Instruments: {task.compatible_instruments?.length || 0}
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Quality Checks: {task.quality_checks?.length || 0}
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Outputs: {task.outputs?.length || 0}
                  </Typography>
                </Box>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Details</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" display="block" fontWeight="bold">Quality Checks:</Typography>
                      <List dense>
                        {task.quality_checks?.map((check, index) => (
                          <ListItem key={index}>
                            <CheckIcon fontSize="small" color="success" sx={{ mr: 1 }} />
                            <ListItemText primary={check} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" display="block" fontWeight="bold">Expected Outputs:</Typography>
                      <List dense>
                        {task.outputs?.map((output, index) => (
                          <ListItem key={index}>
                            <ListItemText primary={output} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  </AccordionDetails>
                </Accordion>

                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <ScheduleIcon fontSize="small" color="action" />
                    <Typography variant="caption" color="text.secondary">
                      ~{Math.round(task.estimated_duration_seconds / 60)}min
                    </Typography>
                  </Box>
                  <Chip
                    label={task.created_by}
                    size="small"
                    color={task.created_by === 'system' ? 'default' : 'secondary'}
                  />
                </Box>
              </CardContent>

              <CardActions>
                <IconButton
                  size="small"
                  onClick={() => handleEditTask(task)}
                  title="Edit task"
                >
                  <EditIcon />
                </IconButton>
                
                {task.created_by !== 'system' && (
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteTask(task.id)}
                    title="Delete task"
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Edit/Create Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedTask ? 'Edit Task' : 'Create New Task'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Task Name"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={formData.category || 'analytical'}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  >
                    {categories.map((cat) => (
                      <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Workflow Position</InputLabel>
                  <Select
                    value={formData.workflow_position || 'intermediate'}
                    onChange={(e) => setFormData({ ...formData, workflow_position: e.target.value })}
                  >
                    {workflowPositions.map((pos) => (
                      <MenuItem key={pos} value={pos}>{pos}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Estimated Duration (seconds)"
                  type="number"
                  value={formData.estimated_duration_seconds || 60}
                  onChange={(e) => setFormData({ ...formData, estimated_duration_seconds: parseInt(e.target.value) })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  multiline
                  rows={3}
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  options={instruments}
                  getOptionLabel={(option) => option.name}
                  value={instruments.filter(inst => formData.compatible_instruments?.includes(inst.id))}
                  onChange={(_, newValue) => {
                    setFormData({
                      ...formData,
                      compatible_instruments: newValue.map(inst => inst.id)
                    });
                  }}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Compatible Instruments"
                      placeholder="Select compatible instruments"
                    />
                  )}
                />
              </Grid>
              
              {/* Quality Checks */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">Quality Checks</Typography>
                  <Button size="small" onClick={addQualityCheck}>
                    <AddIcon /> Add Check
                  </Button>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {formData.quality_checks?.map((check, index) => (
                    <Chip
                      key={index}
                      label={check}
                      onDelete={() => removeQualityCheck(index)}
                      size="small"
                    />
                  ))}
                </Box>
              </Grid>

              {/* Outputs */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">Expected Outputs</Typography>
                  <Button size="small" onClick={addOutput}>
                    <AddIcon /> Add Output
                  </Button>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {formData.outputs?.map((output, index) => (
                    <Chip
                      key={index}
                      label={output}
                      onDelete={() => removeOutput(index)}
                      size="small"
                    />
                  ))}
                </Box>
              </Grid>

              {/* Prerequisites */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">Prerequisites</Typography>
                  <Button size="small" onClick={addPrerequisite}>
                    <AddIcon /> Add Prerequisite
                  </Button>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {formData.prerequisites?.map((prereq, index) => (
                    <Chip
                      key={index}
                      label={prereq}
                      onDelete={() => removePrerequisite(index)}
                      size="small"
                    />
                  ))}
                </Box>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveTask} variant="contained">
            {selectedTask ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaskManagement;