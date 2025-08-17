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
import { taskTemplateAPI } from '../services/api';
import { TaskTemplate, TaskTemplateCreate } from '../types/workflow';

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
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<TaskTemplate | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Form state
  const [formData, setFormData] = useState<TaskTemplateCreate>({
    name: '',
    description: '',
    category: 'analytical',
    type: '',
    required_service_type: '',
    default_parameters: {},
    estimated_duration: 30,
    enabled: true,
  });

  // Fetch task templates
  const fetchTemplates = useCallback(async () => {
    try {
      const data = await taskTemplateAPI.getAll();
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
      await taskTemplateAPI.create(formData);
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
      await taskTemplateAPI.update(selectedTemplate.id, formData);
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
      await taskTemplateAPI.delete(selectedTemplate.id);
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
      name: selectedTemplate.name,
      description: selectedTemplate.description,
      category: selectedTemplate.category,
      type: selectedTemplate.type,
      required_service_type: selectedTemplate.required_service_type || '',
      default_parameters: selectedTemplate.default_parameters,
      estimated_duration: selectedTemplate.estimated_duration,
      enabled: selectedTemplate.enabled,
    });
    setShowEditDialog(true);
    handleMenuClose();
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: 'analytical',
      type: '',
      required_service_type: '',
      default_parameters: {},
      estimated_duration: 30,
      enabled: true,
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
                  {template.required_service_type && (
                    <Chip 
                      label={template.required_service_type} 
                      variant="outlined"
                      size="small"
                    />
                  )}
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="textSecondary">
                    ~{template.estimated_duration} min
                  </Typography>
                  <Chip 
                    label={template.enabled ? 'Enabled' : 'Disabled'} 
                    color={template.enabled ? 'success' : 'default'}
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
              <TextField
                label="Type"
                fullWidth
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                required
              />
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
                label="Required Service Type"
                fullWidth
                value={formData.required_service_type}
                onChange={(e) => setFormData({ ...formData, required_service_type: e.target.value })}
                placeholder="e.g. hplc, gc-ms, liquid-handler"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Estimated Duration (minutes)"
                type="number"
                fullWidth
                value={formData.estimated_duration}
                onChange={(e) => setFormData({ ...formData, estimated_duration: parseInt(e.target.value) || 30 })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateTemplate}
            variant="contained"
            disabled={!formData.name || !formData.type}
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
              <TextField
                label="Type"
                fullWidth
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                required
              />
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
                label="Required Service Type"
                fullWidth
                value={formData.required_service_type}
                onChange={(e) => setFormData({ ...formData, required_service_type: e.target.value })}
                placeholder="e.g. hplc, gc-ms, liquid-handler"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Estimated Duration (minutes)"
                type="number"
                fullWidth
                value={formData.estimated_duration}
                onChange={(e) => setFormData({ ...formData, estimated_duration: parseInt(e.target.value) || 30 })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleEditTemplate}
            variant="contained"
            disabled={!formData.name || !formData.type}
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