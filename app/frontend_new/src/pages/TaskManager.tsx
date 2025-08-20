import React, { useState, useEffect, useCallback } from 'react';
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
  FormControl,
  InputLabel,
  Select,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  MoreVert,
  Schedule,
  Science,
  Assignment,
  Settings,
} from '@mui/icons-material';
import { instrumentManagementAPI } from '../services/api';

const categoryColors = {
  analytical: 'primary',
  preparative: 'secondary',
  processing: 'success',
  storage: 'warning',
} as const;

const categoryIcons = {
  analytical: <Science />,
  preparative: <Assignment />,
  processing: <Settings />,
  storage: <Schedule />,
};

export default function TaskManager() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<any | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Form state
  const [formData, setFormData] = useState<any>({
    id: '',
    name: '',
    description: '',
    category: 'analytical',
    workflow_position: 'analytical',
    compatible_instruments: [],
    parameters: {},
    quality_checks: [],
    outputs: [],
    prerequisites: [],
    estimated_duration_seconds: 1800, // 30 minutes in seconds
    success_criteria: {},
    status: 'active',
    created_by: 'user'
  });

  // Fetch task templates
  const fetchTemplates = useCallback(async () => {
    try {
      const data = await instrumentManagementAPI.getAllTasks();
      setTemplates(data);
      setError(null);
      if (loading) setLoading(false);
    } catch (err) {
      console.error('Error fetching task templates:', err);
      setError('Failed to fetch task templates');
      if (loading) setLoading(false);
    }
  }, [loading]);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, template: TaskTemplate) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setSelectedTemplate(template);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedTemplate(null);
  };

  const handleCreateTemplate = async () => {
    try {
      // Generate ID from name
      const taskId = formData.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
      const taskData = { ...formData, id: `task-${taskId}` };
      
      await instrumentManagementAPI.createTask(taskData);
      showSnackbar('Task template created successfully', 'success');
      setShowCreateDialog(false);
      resetForm();
      fetchTemplates();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to create task template', 'error');
    }
  };

  const handleEditTemplate = async () => {
    if (!selectedTemplate) return;

    try {
      await instrumentManagementAPI.updateTask(selectedTemplate.id, formData);
      showSnackbar('Task template updated successfully', 'success');
      setShowEditDialog(false);
      resetForm();
      handleMenuClose();
      fetchTemplates();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to update task template', 'error');
    }
  };

  const handleDeleteTemplate = async () => {
    if (!selectedTemplate) return;

    try {
      await instrumentManagementAPI.deleteTask(selectedTemplate.id);
      showSnackbar('Task template deleted successfully', 'success');
      handleMenuClose();
      fetchTemplates();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to delete task template', 'error');
    }
  };

  const openEditDialog = () => {
    if (!selectedTemplate) return;
    setFormData({
      id: selectedTemplate.id,
      name: selectedTemplate.name,
      description: selectedTemplate.description,
      category: selectedTemplate.category,
      workflow_position: selectedTemplate.workflow_position || 'analytical',
      compatible_instruments: selectedTemplate.compatible_instruments || [],
      parameters: selectedTemplate.parameters || {},
      quality_checks: selectedTemplate.quality_checks || [],
      outputs: selectedTemplate.outputs || [],
      prerequisites: selectedTemplate.prerequisites || [],
      estimated_duration_seconds: selectedTemplate.estimated_duration_seconds || 1800,
      success_criteria: selectedTemplate.success_criteria || {},
      status: selectedTemplate.status || 'active',
      created_by: selectedTemplate.created_by || 'user'
    });
    setShowEditDialog(true);
    handleMenuClose();
  };

  const resetForm = () => {
    setFormData({
      id: '',
      name: '',
      description: '',
      category: 'analytical',
      workflow_position: 'analytical',
      compatible_instruments: [],
      parameters: {},
      quality_checks: [],
      outputs: [],
      prerequisites: [],
      estimated_duration_seconds: 1800,
      success_criteria: {},
      status: 'active',
      created_by: 'user'
    });
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const closeSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Typography>Loading task templates...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Task Templates
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setShowCreateDialog(true)}
        >
          Create Task Template
        </Button>
      </Box>

      {/* Task Templates Grid */}
      <Grid container spacing={3}>
        {templates.map((template) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={template.id}>
            <Card 
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': { 
                  boxShadow: 4,
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.2s',
              }}
            >
              <CardContent sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {categoryIcons[template.category as keyof typeof categoryIcons] || <Settings />}
                    <Typography variant="h6" noWrap>
                      {template.name}
                    </Typography>
                  </Box>
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuClick(e, template)}
                  >
                    <MoreVert />
                  </IconButton>
                </Box>

                <Typography color="textSecondary" gutterBottom>
                  {template.description}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Chip 
                    label={template.category} 
                    color={categoryColors[template.category as keyof typeof categoryColors] || 'default'}
                    size="small"
                  />
                  <Chip 
                    label={template.workflow_position} 
                    variant="outlined"
                    size="small"
                  />
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="textSecondary">
                    ~{Math.round((template.estimated_duration_seconds || 0) / 60)} min
                  </Typography>
                  <Chip 
                    label={template.status === 'active' ? 'Active' : 'Inactive'} 
                    color={template.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}

        {templates.length === 0 && (
          <Grid item xs={12}>
            <Card sx={{ textAlign: 'center', p: 4 }}>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                No task templates found
              </Typography>
              <Typography color="textSecondary" paragraph>
                Create your first task template to get started with reusable workflow components.
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => setShowCreateDialog(true)}
              >
                Create Your First Task Template
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
        <MenuItem onClick={openEditDialog}>
          <Edit sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDeleteTemplate} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Create Template Dialog */}
      <Dialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Task Template</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Name"
                fullWidth
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Workflow Position</InputLabel>
                <Select
                  value={formData.workflow_position}
                  onChange={(e) => setFormData({ ...formData, workflow_position: e.target.value })}
                >
                  <MenuItem value="initial">Initial</MenuItem>
                  <MenuItem value="analytical">Analytical</MenuItem>
                  <MenuItem value="preparative">Preparative</MenuItem>
                  <MenuItem value="final">Final</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Description"
                fullWidth
                multiline
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <MenuItem value="analytical">Analytical</MenuItem>
                  <MenuItem value="preparative">Preparative</MenuItem>
                  <MenuItem value="processing">Processing</MenuItem>
                  <MenuItem value="storage">Storage</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Estimated Duration (minutes)"
                type="number"
                fullWidth
                value={Math.round(formData.estimated_duration_seconds / 60)}
                onChange={(e) => setFormData({ ...formData, estimated_duration_seconds: (parseInt(e.target.value) || 30) * 60 })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateTemplate}
            variant="contained"
            disabled={!formData.name || !formData.description}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Template Dialog */}
      <Dialog open={showEditDialog} onClose={() => setShowEditDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Task Template</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Name"
                fullWidth
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Workflow Position</InputLabel>
                <Select
                  value={formData.workflow_position}
                  onChange={(e) => setFormData({ ...formData, workflow_position: e.target.value })}
                >
                  <MenuItem value="initial">Initial</MenuItem>
                  <MenuItem value="analytical">Analytical</MenuItem>
                  <MenuItem value="preparative">Preparative</MenuItem>
                  <MenuItem value="final">Final</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Description"
                fullWidth
                multiline
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <MenuItem value="analytical">Analytical</MenuItem>
                  <MenuItem value="preparative">Preparative</MenuItem>
                  <MenuItem value="processing">Processing</MenuItem>
                  <MenuItem value="storage">Storage</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Estimated Duration (minutes)"
                type="number"
                fullWidth
                value={Math.round(formData.estimated_duration_seconds / 60)}
                onChange={(e) => setFormData({ ...formData, estimated_duration_seconds: (parseInt(e.target.value) || 30) * 60 })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleEditTemplate}
            variant="contained"
            disabled={!formData.name || !formData.description}
          >
            Update
          </Button>
        </DialogActions>
      </Dialog>

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

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ position: 'fixed', bottom: 16, left: 16, zIndex: 1300 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}