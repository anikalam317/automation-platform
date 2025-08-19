#!/usr/bin/env node

/**
 * Instrument Simulation Script
 * Simulates laboratory instruments for testing the automation platform
 */

const express = require('express');
const cors = require('cors');

// Simulated instrument configurations
const instruments = {
  hplc: {
    port: 8001,
    name: 'HPLC System A',
    status: 'online',
    capabilities: ['UV Detection', 'Gradient Elution', 'Auto Sampler'],
    currentMethod: null,
    queue: [],
    running: false
  },
  gcms: {
    port: 8002,
    name: 'GC-MS System',
    status: 'online',
    capabilities: ['EI Ionization', 'SIM Mode', 'Temperature Programming'],
    currentMethod: null,
    queue: [],
    running: false
  },
  liquidhandler: {
    port: 8003,
    name: 'Liquid Handler',
    status: 'online',
    capabilities: ['Multi-channel Pipetting', 'Plate Handling'],
    currentMethod: null,
    queue: [],
    running: false
  },
  balance: {
    port: 8004,
    name: 'Analytical Balance',
    status: 'online',
    capabilities: ['Precision Weighing', 'Density Determination'],
    currentMethod: null,
    queue: [],
    running: false
  },
  storage: {
    port: 8005,
    name: 'Sample Storage',
    status: 'online',
    capabilities: ['Temperature Control', 'Barcode Scanning'],
    currentMethod: null,
    queue: [],
    running: false
  }
};

// Create instrument simulators
Object.keys(instruments).forEach(instrumentType => {
  const instrument = instruments[instrumentType];
  const app = express();
  
  app.use(cors());
  app.use(express.json());
  
  // Health check endpoint
  app.get('/health', (req, res) => {
    res.json({
      name: instrument.name,
      status: instrument.status,
      capabilities: instrument.capabilities,
      running: instrument.running,
      queue_length: instrument.queue.length
    });
  });
  
  // Status endpoint
  app.get('/status', (req, res) => {
    res.json({
      status: instrument.status,
      current_method: instrument.currentMethod,
      queue: instrument.queue,
      running: instrument.running
    });
  });
  
  // Execute method endpoint
  app.post('/execute', (req, res) => {
    const { method, parameters, sample_id } = req.body;
    
    if (instrument.running) {
      // Add to queue
      instrument.queue.push({ method, parameters, sample_id, id: Date.now() });
      res.json({
        status: 'queued',
        position: instrument.queue.length,
        estimated_start: new Date(Date.now() + instrument.queue.length * 30000) // 30s per queued job
      });
    } else {
      // Start immediate execution
      instrument.running = true;
      instrument.currentMethod = { method, parameters, sample_id, started: new Date() };
      
      // Simulate execution time
      const executionTime = getExecutionTime(instrumentType, method);
      
      setTimeout(() => {
        instrument.running = false;
        instrument.currentMethod = null;
        
        // Process next in queue
        if (instrument.queue.length > 0) {
          const next = instrument.queue.shift();
          instrument.running = true;
          instrument.currentMethod = { ...next, started: new Date() };
        }
      }, executionTime);
      
      res.json({
        status: 'running',
        estimated_completion: new Date(Date.now() + executionTime),
        execution_id: Date.now()
      });
    }
  });
  
  // Stop/abort endpoint
  app.post('/stop', (req, res) => {
    instrument.running = false;
    instrument.currentMethod = null;
    instrument.queue = [];
    
    res.json({
      status: 'stopped',
      message: 'Instrument stopped and queue cleared'
    });
  });
  
  // Results endpoint (mock data)
  app.get('/results/:execution_id', (req, res) => {
    const executionId = req.params.execution_id;
    
    res.json({
      execution_id: executionId,
      status: 'completed',
      results: generateMockResults(instrumentType),
      timestamp: new Date(),
      data_file: `/data/${instrumentType}_${executionId}.json`
    });
  });
  
  // Start the server
  app.listen(instrument.port, () => {
    console.log(`${instrument.name} simulator running on port ${instrument.port}`);
  });
});

// Helper functions
function getExecutionTime(instrumentType, method) {
  const baseTimes = {
    hplc: 30000,      // 30 seconds for demo (would be 30+ minutes in reality)
    gcms: 45000,      // 45 seconds for demo
    liquidhandler: 15000, // 15 seconds
    balance: 5000,    // 5 seconds
    storage: 3000     // 3 seconds
  };
  
  return baseTimes[instrumentType] || 20000;
}

function generateMockResults(instrumentType) {
  switch (instrumentType) {
    case 'hplc':
      return {
        peaks: Math.floor(Math.random() * 10) + 5,
        retention_times: [5.2, 8.7, 12.3, 15.9].slice(0, Math.floor(Math.random() * 4) + 1),
        peak_areas: [125000, 89000, 156000, 203000].slice(0, Math.floor(Math.random() * 4) + 1),
        resolution: 2.5,
        column_efficiency: 8500
      };
    
    case 'gcms':
      return {
        compounds_detected: Math.floor(Math.random() * 8) + 3,
        base_peak: Math.floor(Math.random() * 500) + 50,
        molecular_ion: Math.floor(Math.random() * 600) + 100,
        library_matches: ['Compound A (95%)', 'Compound B (88%)', 'Compound C (76%)'],
        scan_range: '50-500 m/z'
      };
    
    case 'liquidhandler':
      return {
        volumes_dispensed: [100, 150, 200, 250].map(v => v + Math.random() * 5 - 2.5),
        accuracy: 99.2,
        precision: 0.8,
        tips_used: 96,
        plates_processed: 1
      };
    
    case 'balance':
      return {
        mass: 100.0234,
        units: 'mg',
        stability: 'stable',
        uncertainty: 0.1,
        environment: {
          temperature: 21.5,
          humidity: 45.2
        }
      };
    
    case 'storage':
      return {
        location: `R${Math.floor(Math.random() * 10) + 1}-S${Math.floor(Math.random() * 20) + 1}-P${Math.floor(Math.random() * 100) + 1}`,
        barcode: `BC${Math.floor(Math.random() * 1000000)}`,
        temperature: -20.5,
        logged: true
      };
    
    default:
      return {
        status: 'completed',
        data: 'mock_data_generated'
      };
  }
}

console.log('Starting laboratory instrument simulators...');
console.log('Instruments will be available on the following ports:');
Object.keys(instruments).forEach(type => {
  console.log(`- ${instruments[type].name}: http://localhost:${instruments[type].port}`);
});
console.log('\nPress Ctrl+C to stop all simulators.');

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\nShutting down all instrument simulators...');
  process.exit(0);
});