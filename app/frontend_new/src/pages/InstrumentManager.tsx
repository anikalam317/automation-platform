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
import { serviceAPI } from '../services/api';
import { Service } from '../types/workflow';

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
  const [instruments, setInstruments] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInstrument, setSelectedInstrument] = useState<Service | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: '',
    endpoint: '',
    default_parameters: {},
    enabled: true,
  });

  // Fetch instruments
  const fetchInstruments = useCallback(async () => {
    try {
      const data = await serviceAPI.getAll();
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
      await serviceAPI.create(formData);
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
      await serviceAPI.update(selectedInstrument.id, formData);
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
      await serviceAPI.delete(selectedInstrument.id);
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
      name: selectedInstrument.name,
      description: selectedInstrument.description,
      type: selectedInstrument.type,
      endpoint: selectedInstrument.endpoint,
      default_parameters: selectedInstrument.default_parameters,
      enabled: selectedInstrument.enabled,
    });
    setShowEditDialog(true);
    handleMenuClose();
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      type: '',
      endpoint: '',
      default_parameters: {},
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
                    label={instrument.type} 
                    color={typeColors[instrument.type as keyof typeof typeColors] || 'default'}
                    size="small"
                  />
                  <Chip 
                    label={instrument.enabled ? 'Enabled' : 'Disabled'} 
                    color={instrument.enabled ? 'success' : 'default'}
                    size="small"
                  />
                </Box>

                <Typography variant="caption" color="textSecondary" sx={{ display: 'block' }}>
                  Endpoint: {instrument.endpoint}
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
              <TextField
                label="Type"
                fullWidth
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                required
                placeholder="e.g. hplc, gc-ms, liquid-handler"
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
                placeholder="http://localhost:8001/instrument"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  />
                }
                label="Enabled"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateInstrument}
            variant="contained"
            disabled={!formData.name || !formData.type || !formData.endpoint}
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
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  />
                }
                label="Enabled"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleEditInstrument}
            variant="contained"
            disabled={!formData.name || !formData.type || !formData.endpoint}
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