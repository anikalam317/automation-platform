import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Add,
  PlayArrow,
  Visibility,
  Edit,
  Delete,
  MoreVert,
  Schedule,
  CheckCircle,
  Error,
  Pause,
  Stop,
  PlayCircleOutline,
} from '@mui/icons-material';
import { workflowAPI } from '../services/api';
import { pollingService } from '../services/websocket';
import { validateCompleteWorkflow } from '../utils/validation';
import { Workflow, WorkflowCreate } from '../types/workflow';

const statusIcons = {
  pending: <Schedule color="warning" />,
  running: <PlayArrow color="info" />,
  completed: <CheckCircle color="success" />,
  failed: <Error color="error" />,
  paused: <Pause color="warning" />,
  stopped: <Stop color="error" />,
};

const statusColors = {
  pending: 'warning',
  running: 'info',
  completed: 'success',
  failed: 'error',
  paused: 'warning',
  stopped: 'error',
} as const;

/**
 * WorkflowList Component
 * 
 * Implements polling-based workflow monitoring as per the event-driven architecture:
 * 1. Polls /api/workflows every 2 seconds for status updates
 * 2. Creates workflows with JSON schema validation
 * 3. Workflow creation triggers backend database events
 */
export default function WorkflowList() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState('');
  const [newWorkflowAuthor, setNewWorkflowAuthor] = useState('Lab User');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Fetch workflows function for polling
  const fetchWorkflows = useCallback(async () => {
    try {
      const data = await workflowAPI.getAll();
      setWorkflows(data);
      setError(null);
      if (loading) setLoading(false);
    } catch (err) {
      console.error('[Polling] Error fetching workflows:', err);
      setError('Failed to fetch workflows');
      if (loading) setLoading(false);
    }
  }, [loading]);

  // Start polling for workflow updates (follows architecture pattern)
  useEffect(() => {
    console.log('[WorkflowList] Starting workflow polling');
    
    // Initial fetch
    fetchWorkflows();

    // Start polling every 2 seconds (matches existing frontend pattern)
    pollingService.startPolling(
      'workflows-list',
      fetchWorkflows,
      {
        interval: 2000,
        maxRetries: 3,
        onError: (error) => {
          setError(`Polling failed: ${error.message}`);
          showSnackbar('Connection lost. Retrying...', 'error');
        }
      }
    );

    // Cleanup polling on unmount
    return () => {
      console.log('[WorkflowList] Stopping workflow polling');
      pollingService.stopPolling('workflows-list');
    };
  }, [fetchWorkflows]);

  // Create workflow with validation (triggers event-driven backend flow)
  const handleCreateWorkflow = async () => {
    if (!newWorkflowName.trim()) {
      showSnackbar('Workflow name is required', 'error');
      return;
    }

    try {
      const workflowData: WorkflowCreate = {
        name: newWorkflowName.trim(),
        author: newWorkflowAuthor.trim(),
        tasks: [] // Empty workflow, will be configured in builder
      };

      // Validate before sending (frontend validation)
      const validation = validateCompleteWorkflow(workflowData);
      if (!validation.valid) {
        showSnackbar(`Validation failed: ${validation.formattedErrors?.join(', ')}`, 'error');
        return;
      }

      console.log('[Workflow Creation] Sending POST request to backend');
      console.log('[Event Flow] This will trigger database insertion -> PostgreSQL NOTIFY -> Workflow Coordinator');

      const createdWorkflow = await workflowAPI.create(workflowData);
      
      showSnackbar('Workflow created successfully', 'success');
      setShowCreateDialog(false);
      setNewWorkflowName('');
      
      // Navigate to builder for configuration
      navigate(`/builder/${createdWorkflow.id}`);
      
    } catch (err: any) {
      console.error('[Workflow Creation] Error:', err);
      showSnackbar(err.message || 'Failed to create workflow', 'error');
    }
  };

  // Delete workflow
  const handleDeleteWorkflow = async () => {
    if (!selectedWorkflow) return;

    try {
      await workflowAPI.delete(selectedWorkflow.id);
      showSnackbar('Workflow deleted successfully', 'success');
      setAnchorEl(null);
      setSelectedWorkflow(null);
      // Polling will automatically update the list
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to delete workflow', 'error');
    }
  };

  // Pause workflow
  const handlePauseWorkflow = async (workflowId: number) => {
    try {
      await workflowAPI.pause(workflowId);
      showSnackbar('Workflow paused successfully', 'success');
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to pause workflow', 'error');
    }
  };

  // Stop workflow
  const handleStopWorkflow = async (workflowId: number) => {
    try {
      await workflowAPI.stop(workflowId);
      showSnackbar('Workflow stopped successfully', 'success');
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to stop workflow', 'error');
    }
  };

  // Resume workflow
  const handleResumeWorkflow = async (workflowId: number) => {
    try {
      await workflowAPI.resume(workflowId);
      showSnackbar('Workflow resumed successfully', 'success');
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to resume workflow', 'error');
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const closeSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, workflow: Workflow) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setSelectedWorkflow(workflow);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedWorkflow(null);
  };



  const getProgress = (workflow: Workflow) => {
    if (workflow.tasks.length === 0) return 0;
    const completed = workflow.tasks.filter(task => task.status === 'completed').length;
    return (completed / workflow.tasks.length) * 100;
  };

  const getControlButtons = (workflow: Workflow) => {
    const buttons = [];
    
    if (workflow.status === 'running') {
      buttons.push(
        <Button 
          key="pause"
          size="small" 
          startIcon={<Pause />}
          onClick={(e) => {
            e.stopPropagation();
            handlePauseWorkflow(workflow.id);
          }}
          color="warning"
        >
          Pause
        </Button>
      );
      buttons.push(
        <Button 
          key="stop"
          size="small" 
          startIcon={<Stop />}
          onClick={(e) => {
            e.stopPropagation();
            handleStopWorkflow(workflow.id);
          }}
          color="error"
        >
          Stop
        </Button>
      );
    } else if (workflow.status === 'paused') {
      buttons.push(
        <Button 
          key="resume"
          size="small" 
          startIcon={<PlayCircleOutline />}
          onClick={(e) => {
            e.stopPropagation();
            handleResumeWorkflow(workflow.id);
          }}
          color="success"
        >
          Resume
        </Button>
      );
      buttons.push(
        <Button 
          key="stop"
          size="small" 
          startIcon={<Stop />}
          onClick={(e) => {
            e.stopPropagation();
            handleStopWorkflow(workflow.id);
          }}
          color="error"
        >
          Stop
        </Button>
      );
    }
    
    return buttons;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Typography>Loading workflows...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Workflows
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setShowCreateDialog(true)}
        >
          Create Workflow
        </Button>
      </Box>

      {/* Workflow Grid */}
      <Grid container spacing={3}>
        {workflows.map((workflow) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={workflow.id}>
            <Card 
              sx={{ 
                cursor: 'pointer',
                '&:hover': { 
                  boxShadow: 4,
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.2s',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
              }}
              onClick={() => navigate(`/monitor/${workflow.id}`)}
            >
              <CardContent sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" noWrap>
                    {workflow.name}
                  </Typography>
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuClick(e, workflow)}
                  >
                    <MoreVert />
                  </IconButton>
                </Box>

                <Typography color="textSecondary" gutterBottom>
                  By {workflow.author}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  {statusIcons[workflow.status]}
                  <Chip 
                    label={workflow.status.toUpperCase()} 
                    color={statusColors[workflow.status]}
                    size="small"
                  />
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Progress: {workflow.tasks.filter(t => t.status === 'completed').length} / {workflow.tasks.length} tasks
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={getProgress(workflow)}
                    sx={{ height: 6, borderRadius: 3 }}
                  />
                </Box>

                <Typography variant="caption" color="textSecondary">
                  Created: {new Date(workflow.created_at).toLocaleDateString()}
                </Typography>
              </CardContent>

              <Box sx={{ p: 2, pt: 0, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {/* Control buttons based on status */}
                {getControlButtons(workflow)}
                
                {/* Standard navigation buttons */}
                <Button 
                  size="small" 
                  startIcon={<Visibility />}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/monitor/${workflow.id}`);
                  }}
                >
                  Monitor
                </Button>
                <Button 
                  size="small" 
                  startIcon={<Edit />}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/builder/${workflow.id}`);
                  }}
                >
                  Edit
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}

        {workflows.length === 0 && (
          <Grid item xs={12}>
            <Card sx={{ textAlign: 'center', p: 4 }}>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                No workflows found
              </Typography>
              <Typography color="textSecondary" paragraph>
                Create your first workflow to get started with laboratory automation.
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => setShowCreateDialog(true)}
              >
                Create Your First Workflow
              </Button>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          if (selectedWorkflow) navigate(`/monitor/${selectedWorkflow.id}`);
          handleMenuClose();
        }}>
          <Visibility sx={{ mr: 1 }} />
          Monitor
        </MenuItem>
        <MenuItem onClick={() => {
          if (selectedWorkflow) navigate(`/builder/${selectedWorkflow.id}`);
          handleMenuClose();
        }}>
          <Edit sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDeleteWorkflow} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Create Workflow Dialog */}
      <Dialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)}>
        <DialogTitle>Create New Workflow</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Workflow Name"
            fullWidth
            variant="outlined"
            value={newWorkflowName}
            onChange={(e) => setNewWorkflowName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Author"
            fullWidth
            variant="outlined"
            value={newWorkflowAuthor}
            onChange={(e) => setNewWorkflowAuthor(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateWorkflow}
            variant="contained"
            disabled={!newWorkflowName.trim()}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Error/Success Notifications */}
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

      {/* Connection Status */}
      {error && (
        <Alert severity="error" sx={{ position: 'fixed', bottom: 16, left: 16, zIndex: 1300 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}