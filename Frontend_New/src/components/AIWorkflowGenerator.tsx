import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
} from '@mui/material';
import { AutoAwesome, Close, Send } from '@mui/icons-material';
import { aiAPI } from '../services/api';
import { WorkflowCreate } from '../types/workflow';

interface AIWorkflowGeneratorProps {
  open: boolean;
  onClose: () => void;
  onWorkflowGenerated: (workflow: WorkflowCreate) => void;
}

const samplePrompts = [
  "Create a workflow for HPLC analysis of pharmaceutical samples with automated sample prep",
  "Design a workflow for protein purification using chromatography and analysis",
  "Build a workflow for environmental water testing including extraction and GC-MS analysis",
  "Create a quality control workflow for food safety testing",
  "Design a workflow for chemical synthesis monitoring and product analysis"
];

export default function AIWorkflowGenerator({ 
  open, 
  onClose, 
  onWorkflowGenerated 
}: AIWorkflowGeneratorProps) {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const workflow = await aiAPI.generateWorkflow(prompt);
      onWorkflowGenerated(workflow);
      setPrompt('');
      onClose();
    } catch (err) {
      setError('Failed to generate workflow. Please try again.');
      console.error('AI generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePromptSelect = (selectedPrompt: string) => {
    setPrompt(selectedPrompt);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      handleGenerate();
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2 }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, pb: 1 }}>
        <AutoAwesome color="primary" />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AI Workflow Generator
        </Typography>
        <IconButton onClick={onClose} size="small">
          <Close />
        </IconButton>
      </DialogTitle>
      
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Describe your laboratory workflow in natural language, and our AI will generate 
          the appropriate sequence of tasks and instruments.
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <TextField
          fullWidth
          multiline
          rows={4}
          placeholder="Describe your workflow... (e.g., 'Create a workflow for HPLC analysis with automated sample preparation and data processing')"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          sx={{ mb: 2 }}
        />
        
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Sample prompts:
        </Typography>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
          {samplePrompts.map((samplePrompt, index) => (
            <Chip
              key={index}
              label={samplePrompt}
              onClick={() => handlePromptSelect(samplePrompt)}
              variant="outlined"
              size="small"
              sx={{
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: 'primary.light',
                  color: 'white',
                },
              }}
            />
          ))}
        </Box>
        
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Tip:</strong> Be specific about your requirements including:
            <br />• Sample types and preparation methods
            <br />• Analytical techniques needed
            <br />• Data processing requirements
            <br />• Quality control steps
          </Typography>
        </Alert>
      </DialogContent>
      
      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleGenerate}
          disabled={!prompt.trim() || loading}
          startIcon={loading ? <CircularProgress size={16} /> : <Send />}
          sx={{ minWidth: 120 }}
        >
          {loading ? 'Generating...' : 'Generate Workflow'}
        </Button>
      </DialogActions>
      
      <Box sx={{ p: 1, backgroundColor: 'grey.50', borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary">
          Press Ctrl+Enter to generate • AI responses may take a few moments
        </Typography>
      </Box>
    </Dialog>
  );
}