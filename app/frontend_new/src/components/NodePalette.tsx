import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, 
  Typography, 
  List, 
  ListItem, 
  ListItemText, 
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import { 
  ExpandMore, 
  Science, 
  Storage, 
  Biotech, 
  Computer,
  Assignment,
  Settings,
  Memory
} from '@mui/icons-material';
import { taskTemplateAPI, serviceAPI } from '../services/api';
import { TaskTemplate, Service } from '../types/workflow';

interface NodeTemplate {
  id: string;
  type: 'task' | 'instrument';
  label: string;
  description: string;
  category: string;
  icon: React.ReactNode;
  defaultParameters?: Record<string, any>;
  sourceData?: TaskTemplate | Service; // Reference to original data
}

// Icon mapping for categories and types
const categoryIcons = {
  analytical: <Science />,
  preparative: <Biotech />,
  storage: <Storage />,
  processing: <Computer />,
  control: <Settings />,
  default: <Assignment />
};

const serviceTypeIcons = {
  hplc: <Science />,
  'gc-ms': <Science />,
  'liquid-handler': <Biotech />,
  balance: <Biotech />,
  storage: <Storage />,
  default: <Memory />
};

// Utility function to extract default values from parameter schema
const extractDefaultParameters = (parameters: Record<string, any>) => {
  const defaultValues: Record<string, any> = {};
  
  for (const [key, param] of Object.entries(parameters)) {
    if (param && typeof param === 'object' && param.default !== undefined) {
      defaultValues[key] = param.default;
    } else if (param && typeof param === 'object' && param.type) {
      // Handle different parameter types with sensible defaults
      switch (param.type) {
        case 'string':
          defaultValues[key] = param.default || '';
          break;
        case 'number':
          defaultValues[key] = param.default || param.min || 0;
          break;
        case 'boolean':
          defaultValues[key] = param.default || false;
          break;
        case 'select':
          defaultValues[key] = param.default || (param.options && param.options[0]) || '';
          break;
        default:
          if (param.default !== undefined) {
            defaultValues[key] = param.default;
          }
      }
    }
  }
  
  return defaultValues;
};


interface NodePaletteProps {
  onDragStart: (event: React.DragEvent, nodeTemplate: NodeTemplate) => void;
}

export default function NodePalette({ onDragStart }: NodePaletteProps) {
  const [taskTemplates, setTaskTemplates] = useState<TaskTemplate[]>([]);
  const [instruments, setInstruments] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data function
  const fetchData = useCallback(async () => {
    try {
      // Try to get data from the new instrument management API first
      let templates = taskTemplates;
      let services = instruments;
      
      try {
        // Fetch from new instrument management API
        const paletteResponse = await fetch('/api/instrument-management/node-palette');
        if (paletteResponse.ok) {
          const paletteData = await paletteResponse.json();
          
          // Convert new API data to existing format for backwards compatibility
          if (paletteData.tasks) {
            templates = paletteData.tasks.map((task: any) => ({
              id: task.id,
              name: task.name,
              description: task.description,
              category: task.category,
              default_parameters: extractDefaultParameters(task.parameters || {}),
              estimated_duration: Math.round(task.estimated_duration / 60) // Convert to minutes
            }));
          }
          
          if (paletteData.instruments) {
            services = paletteData.instruments.map((instrument: any) => ({
              id: instrument.id,
              name: instrument.name,
              description: instrument.description,
              type: instrument.category,
              default_parameters: extractDefaultParameters(instrument.parameters || {})
            }));
          }
        }
      } catch (paletteError) {
        console.warn('New instrument management API not available, falling back to legacy APIs');
        
        // Fallback to existing APIs
        const [legacyTemplates, legacyServices] = await Promise.all([
          taskTemplateAPI.getAll(),
          serviceAPI.getAll()
        ]);
        templates = legacyTemplates;
        services = legacyServices;
      }
      
      setTaskTemplates(templates);
      setInstruments(services);
      setError(null);
    } catch (err) {
      console.error('Error fetching palette data:', err);
      setError('Failed to load components');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch data on mount
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Refetch data when component comes back into view (e.g., navigating back to Builder)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchData();
      }
    };

    const handleFocus = () => {
      fetchData();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [fetchData]);

  // Convert task templates to node templates
  const taskNodeTemplates: NodeTemplate[] = taskTemplates.map(template => ({
    id: `task-${template.id}`,
    type: 'task' as const,
    label: template.name,
    description: template.description,
    category: template.category,
    icon: categoryIcons[template.category as keyof typeof categoryIcons] || categoryIcons.default,
    defaultParameters: template.default_parameters,
    sourceData: template
  }));

  // Convert instruments to node templates  
  const instrumentNodeTemplates: NodeTemplate[] = instruments.map(instrument => ({
    id: `instrument-${instrument.id}`,
    type: 'instrument' as const,
    label: instrument.name,
    description: instrument.description,
    category: 'instruments', // Group all instruments together
    icon: serviceTypeIcons[instrument.type as keyof typeof serviceTypeIcons] || serviceTypeIcons.default,
    defaultParameters: instrument.default_parameters,
    sourceData: instrument
  }));


  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress size={24} />
        <Typography sx={{ ml: 1 }}>Loading...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', overflow: 'auto' }}>
      <Typography variant="h6" sx={{ p: 2, fontWeight: 'bold' }}>
        Workflow Components
      </Typography>
      
      {/* Task Templates Section */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Assignment color="primary" />
            <Typography variant="subtitle1" fontWeight="bold">
              Task Templates
            </Typography>
            <Chip size="small" label={taskTemplates.length} />
          </Box>
        </AccordionSummary>
        <AccordionDetails sx={{ p: 0 }}>
          {/* Group task templates by category */}
          {[...new Set(taskTemplates.map(t => t.category))].map(category => (
            <Box key={category}>
              <Typography 
                variant="caption" 
                sx={{ 
                  px: 2, 
                  py: 1, 
                  display: 'block', 
                  backgroundColor: '#f5f5f5',
                  textTransform: 'uppercase',
                  fontWeight: 'bold'
                }}
              >
                {category}
              </Typography>
              <List dense>
                {taskNodeTemplates
                  .filter(template => (template.sourceData as TaskTemplate)?.category === category)
                  .map(template => (
                    <ListItem 
                      key={template.id}
                      sx={{ 
                        cursor: 'grab',
                        '&:hover': { backgroundColor: '#f5f5f5' },
                        py: 0.5
                      }}
                      draggable
                      onDragStart={(event) => onDragStart(event, template)}
                    >
                      <Paper
                        elevation={1}
                        sx={{
                          p: 1,
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          border: '1px solid #e0e0e0',
                          borderRadius: 1,
                          backgroundColor: '#fafafa'
                        }}
                      >
                        <Box sx={{ color: '#1976d2' }}>
                          {template.icon}
                        </Box>
                        <ListItemText
                          primary={template.label}
                          secondary={`${template.description} • ~${(template.sourceData as TaskTemplate)?.estimated_duration}min`}
                          primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: 500 }}
                          secondaryTypographyProps={{ fontSize: '0.7rem' }}
                        />
                      </Paper>
                    </ListItem>
                  ))}
              </List>
            </Box>
          ))}
        </AccordionDetails>
      </Accordion>

      {/* Instruments Section */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Memory color="secondary" />
            <Typography variant="subtitle1" fontWeight="bold">
              Instruments & Services
            </Typography>
            <Chip size="small" label={instruments.length} />
          </Box>
        </AccordionSummary>
        <AccordionDetails sx={{ p: 0 }}>
          <List dense>
            {instrumentNodeTemplates.map(template => (
              <ListItem 
                key={template.id}
                sx={{ 
                  cursor: 'grab',
                  '&:hover': { backgroundColor: '#f5f5f5' },
                  py: 0.5
                }}
                draggable
                onDragStart={(event) => onDragStart(event, template)}
              >
                <Paper
                  elevation={1}
                  sx={{
                    p: 1,
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    border: '1px solid #e0e0e0',
                    borderRadius: 1,
                    backgroundColor: '#fff3e0'
                  }}
                >
                  <Box sx={{ color: '#f57c00' }}>
                    {template.icon}
                  </Box>
                  <ListItemText
                    primary={template.label}
                    secondary={`${template.description} • ${(template.sourceData as Service)?.type}`}
                    primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: 500 }}
                    secondaryTypographyProps={{ fontSize: '0.7rem' }}
                  />
                </Paper>
              </ListItem>
            ))}
          </List>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}