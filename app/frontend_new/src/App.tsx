import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, AppBar, Toolbar, Typography, Button } from '@mui/material';
import { useWorkflowStore } from './store/workflowStore';
import { pollingService } from './services/websocket'; // Now renamed to polling service
import WorkflowBuilder from './pages/WorkflowBuilder';
import WorkflowMonitor from './pages/WorkflowMonitor';
import InstrumentManager from './pages/InstrumentManager';
import TaskManager from './pages/TaskManager';
import WorkflowList from './pages/WorkflowList';
import './index.css';

/**
 * Main App Component
 * 
 * Follows the event-driven architecture:
 * 1. User creates workflows through the interface
 * 2. Frontend validates using JSON schema
 * 3. Sends POST request to backend
 * 4. Backend creates workflow in database (triggers PostgreSQL NOTIFY)
 * 5. Notification listener starts workflow execution
 * 6. Frontend polls for status updates
 */
function App() {
  const { reset } = useWorkflowStore();

  useEffect(() => {
    console.log('[LAF] Starting Laboratory Automation Framework');
    console.log('[Architecture] Event-driven with PostgreSQL NOTIFY/LISTEN backend');
    console.log('[Frontend] Polling-based status updates');

    // Cleanup on unmount - stop all polling
    return () => {
      console.log('[LAF] Shutting down frontend services');
      pollingService.stopAllPolling();
      reset();
    };
  }, [reset]);

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Laboratory Automation Framework
          </Typography>
          <Button color="inherit" href="/">
            Workflows
          </Button>
          <Button color="inherit" href="/builder">
            Builder
          </Button>
          <Button color="inherit" href="/monitor">
            Monitor
          </Button>
          <Button color="inherit" href="/tasks">
            Tasks
          </Button>
          <Button color="inherit" href="/instruments">
            Instruments
          </Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <Routes>
          <Route path="/" element={<WorkflowList />} />
          <Route path="/builder" element={<WorkflowBuilder />} />
          <Route path="/builder/:id" element={<WorkflowBuilder />} />
          <Route path="/monitor" element={<WorkflowMonitor />} />
          <Route path="/monitor/:id" element={<WorkflowMonitor />} />
          <Route path="/tasks" element={<TaskManager />} />
          <Route path="/instruments" element={<InstrumentManager />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default App;