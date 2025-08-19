import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  PlayArrow,
  CheckCircle,
  Error,
  Schedule,
  ExpandMore,
  Refresh,
  Visibility,
  Download,
} from '@mui/icons-material';
import { workflowAPI } from '../services/api';
import { pollingService } from '../services/websocket';
import { Workflow } from '../types/workflow';

const statusIcons = {
  pending: <Schedule color="warning" />,
  running: <PlayArrow color="info" />,
  completed: <CheckCircle color="success" />,
  failed: <Error color="error" />,
  paused: <Schedule color="warning" />,
  stopped: <Error color="error" />,
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
 * WorkflowMonitor Component
 * 
 * Monitors workflow execution using polling architecture:
 * 1. Polls workflow status every 1 second for real-time monitoring
 * 2. Shows progress of tasks being executed by backend workflow coordinator
 * 3. Displays results from Celery/Kubernetes job execution
 */
export default function WorkflowMonitor() {
  const { id } = useParams();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [executionStatus, setExecutionStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch workflow execution status for monitoring
  const fetchExecutionStatus = useCallback(async () => {
    if (!id) return;

    try {
      const workflowId = parseInt(id);
      const status = await workflowAPI.getExecutionStatus(workflowId);
      
      setWorkflow(status.workflow);
      setExecutionStatus(status);
      setError(null);
      setLastUpdated(new Date());
      
      if (loading) setLoading(false);
      
      console.log('[Monitor] Workflow status updated:', {
        id: workflowId,
        status: status.workflow.status,
        progress: status.progress,
        currentTask: status.currentTask?.name,
        timestamp: new Date().toISOString()
      });
      
    } catch (err: any) {
      console.error('[Monitor] Error fetching execution status:', err);
      setError(`Failed to fetch workflow status: ${err.message}`);
      if (loading) setLoading(false);
    }
  }, [id, loading]);

  // Start polling for workflow execution updates
  useEffect(() => {
    if (!id) return;

    const workflowId = parseInt(id);
    console.log(`[Monitor] Starting monitoring for workflow ${workflowId}`);
    console.log('[Architecture] Polling backend for status updates from event-driven execution');

    // Initial fetch
    fetchExecutionStatus();

    // Start intensive polling for monitoring (1 second for real-time feel)
    pollingService.startPolling(
      `workflow-monitor-${workflowId}`,
      fetchExecutionStatus,
      {
        interval: 1000, // 1 second for real-time monitoring
        maxRetries: 5,
        onError: (error) => {
          setError(`Monitoring failed: ${error.message}`);
        }
      }
    );

    // Cleanup on unmount
    return () => {
      console.log(`[Monitor] Stopping monitoring for workflow ${workflowId}`);
      pollingService.stopPolling(`workflow-monitor-${workflowId}`);
    };
  }, [id, fetchExecutionStatus]);

  // Manual refresh function
  const handleRefresh = () => {
    console.log('[Monitor] Manual refresh triggered');
    fetchExecutionStatus();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Typography>Loading workflow monitoring...</Typography>
      </Box>
    );
  }

  if (!workflow) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Typography>Workflow not found</Typography>
      </Box>
    );
  }

  const completedTasks = executionStatus?.completedTasks?.length || 0;
  const totalTasks = workflow.tasks.length;
  const progress = executionStatus?.progress || 0;
  const currentTask = executionStatus?.currentTask;
  const nextTask = executionStatus?.pendingTasks?.[0];

  return (
    <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {workflow.name}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh}>
              <Refresh />
            </IconButton>
          </Tooltip>
          <Tooltip title="Download Report">
            <IconButton>
              <Download />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Overview Cards */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Status
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {statusIcons[workflow.status]}
                <Chip 
                  label={workflow.status.toUpperCase()} 
                  color={statusColors[workflow.status]}
                  variant="filled"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Progress
              </Typography>
              <Typography variant="h6">
                {completedTasks} / {totalTasks} Tasks
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={progress} 
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Author
              </Typography>
              <Typography variant="h6">
                {workflow.author}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Started
              </Typography>
              <Typography variant="h6">
                {new Date(workflow.created_at).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Current Activity */}
        {(currentTask || nextTask) && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Activity
                </Typography>
                {currentTask && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PlayArrow color="info" />
                      Running: {currentTask.name}
                    </Typography>
                    <LinearProgress sx={{ mt: 1 }} />
                  </Box>
                )}
                {nextTask && (
                  <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Schedule color="warning" />
                    Next: {nextTask.name}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Task List */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Task Details
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Order</TableCell>
                      <TableCell>Task Name</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Executed At</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {workflow.tasks
                      .sort((a, b) => a.order_index - b.order_index)
                      .map((task) => (
                        <TableRow key={task.id}>
                          <TableCell>{task.order_index + 1}</TableCell>
                          <TableCell>{task.name}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {statusIcons[task.status]}
                              <Chip 
                                label={task.status} 
                                color={statusColors[task.status]}
                                size="small"
                              />
                            </Box>
                          </TableCell>
                          <TableCell>
                            {new Date(task.executed_at).toLocaleString()}
                          </TableCell>
                          <TableCell>
                            <Tooltip title="View Results">
                              <IconButton size="small">
                                <Visibility />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Results Panel */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: 'fit-content' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Results & Logs
              </Typography>
              
              {workflow.tasks
                .filter(task => task.results && task.results.length > 0)
                .map((task) => (
                  <Accordion key={task.id}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography variant="subtitle1">{task.name}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List dense>
                        {task.results?.map((result) => (
                          <ListItem key={result.id}>
                            <ListItemIcon>
                              <CheckCircle color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText
                              primary={`Result ${result.id}`}
                              secondary={new Date(result.created_at).toLocaleString()}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                ))}
              
              {workflow.tasks.every(task => !task.results || task.results.length === 0) && (
                <Typography color="textSecondary" align="center" sx={{ py: 2 }}>
                  No results available yet
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Real-time Status Info */}
      {lastUpdated && (
        <Box sx={{ position: 'fixed', bottom: 16, right: 16, zIndex: 1000 }}>
          <Alert severity="info" variant="outlined" sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}>
            Last updated: {lastUpdated.toLocaleTimeString()}
            {pollingService.isPolling(`workflow-monitor-${id}`) && ' • Live monitoring active'}
          </Alert>
        </Box>
      )}

      {/* Error Status */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ position: 'fixed', bottom: 16, left: 16, zIndex: 1000 }}
        >
          {error}
        </Alert>
      )}
    </Box>
  );
}