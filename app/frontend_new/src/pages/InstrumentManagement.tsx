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
  AccordionDetails
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Science as ScienceIcon,
  PlayArrow as TestIcon,
  Sync as SyncIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

interface InstrumentDefinition {
  id: string;
  name: string;
  category: string;
  manufacturer?: string;
  model?: string;
  description: string;
  capabilities: string[];
  parameters: Record<string, any>;
  connection: {
    type: string;
    simulation_endpoint: string;
    real_endpoint?: string;
  };
  typical_runtime_seconds: number;
  status: string;
  created_by: string;
  created_at?: string;
  updated_at?: string;
}

const InstrumentManagement: React.FC = () => {
  const [instruments, setInstruments] = useState<InstrumentDefinition[]>([]);
  const [selectedInstrument, setSelectedInstrument] = useState<InstrumentDefinition | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state for creating/editing instruments
  const [formData, setFormData] = useState<Partial<InstrumentDefinition>>({
    name: '',
    category: 'analytical',
    manufacturer: '',
    model: '',
    description: '',
    capabilities: [],
    parameters: {},
    connection: {
      type: 'http',
      simulation_endpoint: ''
    },
    typical_runtime_seconds: 60,
    status: 'active'
  });

  const categories = [
    'analytical',
    'preparative',
    'processing',
    'storage',
    'measurement'
  ];

  useEffect(() => {
    fetchInstruments();
  }, []);

  const fetchInstruments = async () => {
    try {
      const response = await fetch('/api/instrument-management/instruments');
      if (response.ok) {
        const data = await response.json();
        setInstruments(data);
      } else {
        throw new Error('Failed to fetch instruments');
      }
    } catch (err) {
      setError('Failed to load instruments');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInstrument = () => {
    setFormData({
      name: '',
      category: 'analytical',
      manufacturer: '',
      model: '',
      description: '',
      capabilities: [],
      parameters: {},
      connection: {
        type: 'http',
        simulation_endpoint: ''
      },
      typical_runtime_seconds: 60,
      status: 'active'
    });
    setSelectedInstrument(null);
    setEditDialogOpen(true);
  };

  const handleEditInstrument = (instrument: InstrumentDefinition) => {
    setFormData(instrument);
    setSelectedInstrument(instrument);
    setEditDialogOpen(true);
  };

  const handleSaveInstrument = async () => {
    try {
      if (!formData.id) {
        // Generate ID from name
        formData.id = formData.name?.toLowerCase().replace(/\\s+/g, '-').replace(/[^a-z0-9-]/g, '') || '';
      }

      const method = selectedInstrument ? 'PUT' : 'POST';
      const url = selectedInstrument 
        ? `/api/instrument-management/instruments/${selectedInstrument.id}`
        : '/api/instrument-management/instruments';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setSuccess(selectedInstrument ? 'Instrument updated successfully' : 'Instrument created successfully');
        setEditDialogOpen(false);
        fetchInstruments(); // Refresh list
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save instrument');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save instrument');
    }
  };

  const handleDeleteInstrument = async (instrumentId: string) => {
    if (!confirm('Are you sure you want to delete this instrument?')) return;

    try {
      const response = await fetch(`/api/instrument-management/instruments/${instrumentId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setSuccess('Instrument deleted successfully');
        fetchInstruments(); // Refresh list
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete instrument');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete instrument');
    }
  };

  const handleSyncToDatabase = async () => {
    try {
      const response = await fetch('/api/instrument-management/sync-to-database', {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        setSuccess(result.message);
      } else {
        throw new Error('Failed to sync to database');
      }
    } catch (err) {
      setError('Failed to sync instruments to database');
    }
  };

  const addCapability = () => {
    const capability = prompt('Enter new capability:');
    if (capability) {
      setFormData({
        ...formData,
        capabilities: [...(formData.capabilities || []), capability]
      });
    }
  };

  const removeCapability = (index: number) => {
    setFormData({
      ...formData,
      capabilities: formData.capabilities?.filter((_, i) => i !== index) || []
    });
  };

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>Loading instruments...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ScienceIcon /> Laboratory Instrument Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<SyncIcon />}
            onClick={handleSyncToDatabase}
          >
            Sync to Database
          </Button>
          <Fab
            color="primary"
            aria-label="add"
            onClick={handleCreateInstrument}
          >
            <AddIcon />
          </Fab>
        </Box>
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
        Manage your laboratory instruments. Add new instruments, configure existing ones, and they will automatically 
        appear in the workflow builder node palette.
      </Typography>

      <Grid container spacing={3}>
        {instruments.map((instrument) => (
          <Grid item xs={12} md={6} lg={4} key={instrument.id}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" component="h3">
                    {instrument.name}
                  </Typography>
                  <Chip
                    label={instrument.category}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                </Box>

                {instrument.manufacturer && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {instrument.manufacturer} {instrument.model}
                  </Typography>
                )}

                <Typography variant="body2" sx={{ mb: 2 }}>
                  {instrument.description}
                </Typography>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Capabilities ({instrument.capabilities?.length || 0})</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {instrument.capabilities?.map((capability, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={capability} />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>

                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Runtime: ~{Math.round(instrument.typical_runtime_seconds / 60)}min
                  </Typography>
                  <Chip
                    label={instrument.created_by}
                    size="small"
                    color={instrument.created_by === 'system' ? 'default' : 'secondary'}
                  />
                </Box>
              </CardContent>

              <CardActions>
                <IconButton
                  size="small"
                  onClick={() => handleEditInstrument(instrument)}
                  title="Edit instrument"
                >
                  <EditIcon />
                </IconButton>
                
                {instrument.created_by !== 'system' && (
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteInstrument(instrument.id)}
                    title="Delete instrument"
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                )}

                <IconButton size="small" title="Test connection">
                  <TestIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Edit/Create Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedInstrument ? 'Edit Instrument' : 'Create New Instrument'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Instrument Name"
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
                <TextField
                  fullWidth
                  label="Manufacturer"
                  value={formData.manufacturer || ''}
                  onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Model"
                  value={formData.model || ''}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
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
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Simulation Endpoint"
                  value={formData.connection?.simulation_endpoint || ''}
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    connection: { 
                      ...formData.connection!, 
                      simulation_endpoint: e.target.value 
                    } 
                  })}
                  placeholder="http://instrument-name:port"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Typical Runtime (seconds)"
                  type="number"
                  value={formData.typical_runtime_seconds || 60}
                  onChange={(e) => setFormData({ ...formData, typical_runtime_seconds: parseInt(e.target.value) })}
                />
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">Capabilities</Typography>
                  <Button size="small" onClick={addCapability}>
                    <AddIcon /> Add Capability
                  </Button>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {formData.capabilities?.map((capability, index) => (
                    <Chip
                      key={index}
                      label={capability}
                      onDelete={() => removeCapability(index)}
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
          <Button onClick={handleSaveInstrument} variant="contained">
            {selectedInstrument ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InstrumentManagement;