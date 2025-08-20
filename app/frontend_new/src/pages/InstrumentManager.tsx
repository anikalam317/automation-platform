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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  Menu,
} from '@mui/material';
import {
  Add,
  Settings,
  CheckCircle,
  Error,
  Science,
  Storage,
  Biotech,
  Computer,
  Edit,
  Delete,
  MoreVert,
} from '@mui/icons-material';
import { instrumentManagementAPI } from '../services/api';

const categoryIcons = {
  analytical: <Science />,
  preparative: <Biotech />,
  storage: <Storage />,
  processing: <Computer />,
};

const typeColors = {
  hplc: 'primary',
  'gc-ms': 'secondary', 
  'liquid-handler': 'warning',
  storage: 'success',
} as const;

export default function InstrumentManager() {
  const [instruments, setInstruments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInstrument, setSelectedInstrument] = useState<any | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Form state
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    category: 'analytical',
    manufacturer: '',
    model: '',
    description: '',
    capabilities: [],
    parameters: {},
    connection: {
      type: 'http',
      simulation_endpoint: '',
      real_endpoint: null,
      status_endpoint: '/status',
      execute_endpoint: '/execute',
      results_endpoint: '/results',
      reset_endpoint: '/reset'
    },
    validation: {},
    outputs: {},
    typical_runtime_seconds: 120,
    status: 'active',
    created_by: 'user'
  });

  // Fetch instruments
  const fetchInstruments = useCallback(async () => {
    try {
      const data = await instrumentManagementAPI.getAllInstruments();
      setInstruments(data);
      setError(null);
      if (loading) setLoading(false);
    } catch (err) {
      console.error('Error fetching instruments:', err);
      setError('Failed to fetch instruments');
      if (loading) setLoading(false);
    }
  }, [loading]);

  useEffect(() => {
    fetchInstruments();
  }, [fetchInstruments]);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, instrument: Service) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setSelectedInstrument(instrument);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedInstrument(null);
  };

  const handleCreateInstrument = async () => {
    try {
      // Generate ID from name
      const instrumentId = formData.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
      const instrumentData = { ...formData, id: instrumentId };
      
      await instrumentManagementAPI.createInstrument(instrumentData);
      showSnackbar('Instrument created successfully', 'success');
      setShowCreateDialog(false);
      resetForm();
      fetchInstruments();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to create instrument', 'error');
    }
  };

  const handleEditInstrument = async () => {
    if (!selectedInstrument) return;

    try {
      await instrumentManagementAPI.updateInstrument(selectedInstrument.id, formData);
      showSnackbar('Instrument updated successfully', 'success');
      setShowEditDialog(false);
      resetForm();
      handleMenuClose();
      fetchInstruments();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to update instrument', 'error');
    }
  };

  const handleDeleteInstrument = async () => {
    if (!selectedInstrument) return;

    try {
      await instrumentManagementAPI.deleteInstrument(selectedInstrument.id);
      showSnackbar('Instrument deleted successfully', 'success');
      handleMenuClose();
      fetchInstruments();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to delete instrument', 'error');
    }
  };

  const openEditDialog = () => {
    if (!selectedInstrument) return;
    setFormData({
      id: selectedInstrument.id,
      name: selectedInstrument.name,
      category: selectedInstrument.category || 'analytical',
      manufacturer: selectedInstrument.manufacturer || '',
      model: selectedInstrument.model || '',
      description: selectedInstrument.description,
      capabilities: selectedInstrument.capabilities || [],
      parameters: selectedInstrument.parameters || {},
      connection: selectedInstrument.connection || {
        type: 'http',
        simulation_endpoint: '',
        real_endpoint: null,
        status_endpoint: '/status',
        execute_endpoint: '/execute',
        results_endpoint: '/results',
        reset_endpoint: '/reset'
      },
      validation: selectedInstrument.validation || {},
      outputs: selectedInstrument.outputs || {},
      typical_runtime_seconds: selectedInstrument.typical_runtime_seconds || 120,
      status: selectedInstrument.status || 'active',
      created_by: selectedInstrument.created_by || 'user'
    });
    setShowEditDialog(true);
    handleMenuClose();
  };

  const resetForm = () => {
    setFormData({
      id: '',
      name: '',
      category: 'analytical',
      manufacturer: '',
      model: '',
      description: '',
      capabilities: [],
      parameters: {},
      connection: {
        type: 'http',
        simulation_endpoint: '',
        real_endpoint: null,
        status_endpoint: '/status',
        execute_endpoint: '/execute',
        results_endpoint: '/results',
        reset_endpoint: '/reset'
      },
      validation: {},
      outputs: {},
      typical_runtime_seconds: 120,
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
        <Typography>Loading instruments...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Instruments & Services
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setShowCreateDialog(true)}
        >
          Add Instrument
        </Button>
      </Box>

      {/* Instruments Grid */}
      <Grid container spacing={3}>
        {instruments.map((instrument) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={instrument.id}>
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
                    {categoryIcons.analytical}
                    <Typography variant="h6" noWrap>
                      {instrument.name}
                    </Typography>
                  </Box>
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuClick(e, instrument)}
                  >
                    <MoreVert />
                  </IconButton>
                </Box>

                <Typography color="textSecondary" gutterBottom>
                  {instrument.description}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Chip 
                    label={instrument.category} 
                    color={typeColors[instrument.category as keyof typeof typeColors] || 'default'}
                    size="small"
                  />
                  <Chip 
                    label={instrument.status === 'active' ? 'Active' : 'Inactive'} 
                    color={instrument.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>

                <Typography variant="caption" color="textSecondary" sx={{ display: 'block' }}>
                  Runtime: ~{Math.round((instrument.typical_runtime_seconds || 0) / 60)} min
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}

        {instruments.length === 0 && (
          <Grid item xs={12}>
            <Card sx={{ textAlign: 'center', p: 4 }}>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                No instruments found
              </Typography>
              <Typography color="textSecondary" paragraph>
                Add your first instrument to get started with laboratory automation.
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => setShowCreateDialog(true)}
              >
                Add Your First Instrument
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
        <MenuItem onClick={handleDeleteInstrument} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Create Instrument Dialog */}
      <Dialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Instrument</DialogTitle>
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
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <MenuItem value="analytical">Analytical</MenuItem>
                  <MenuItem value="preparative">Preparative</MenuItem>
                  <MenuItem value="storage">Storage</MenuItem>
                  <MenuItem value="processing">Processing</MenuItem>
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
              <TextField
                label="Manufacturer"
                fullWidth
                value={formData.manufacturer}
                onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                placeholder="e.g. Agilent, Waters, Thermo"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Model"
                fullWidth
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                placeholder="e.g. 1260 Infinity II"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Simulation Endpoint"
                fullWidth
                value={formData.connection.simulation_endpoint}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  connection: { ...formData.connection, simulation_endpoint: e.target.value }
                })}
                required
                placeholder="e.g. http://instrument-service:5001"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateInstrument}
            variant="contained"
            disabled={!formData.name || !formData.connection.simulation_endpoint}
          >
            Add Instrument
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Instrument Dialog */}
      <Dialog open={showEditDialog} onClose={() => setShowEditDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Instrument</DialogTitle>
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
            <Grid item xs={12}>
              <TextField
                label="Endpoint URL"
                fullWidth
                value={formData.endpoint}
                onChange={(e) => setFormData({ ...formData, endpoint: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleEditInstrument}
            variant="contained"
            disabled={!formData.name || !formData.connection.simulation_endpoint}
          >
            Update Instrument
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