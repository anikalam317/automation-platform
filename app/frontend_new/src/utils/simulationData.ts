// Simulation data and utilities for testing workflows

export interface SimulatedInstrument {
  id: string;
  name: string;
  type: string;
  category: 'analytical' | 'preparative' | 'storage' | 'processing';
  status: 'online' | 'offline' | 'busy' | 'error';
  capabilities: string[];
  parameters: Record<string, any>;
  endpoint: string;
}

export interface SimulatedTask {
  id: string;
  name: string;
  type: 'analysis' | 'preparation' | 'storage' | 'processing';
  instrumentType: string;
  duration: number; // in seconds
  parameters: Record<string, any>;
  sampleInputs: string[];
  sampleOutputs: string[];
}

export const simulatedInstruments: SimulatedInstrument[] = [
  {
    id: 'hplc-001',
    name: 'HPLC System A',
    type: 'hplc',
    category: 'analytical',
    status: 'online',
    capabilities: ['UV Detection', 'Gradient Elution', 'Auto Sampler', 'Temperature Control'],
    parameters: {
      maxPressure: 600,
      minFlowRate: 0.1,
      maxFlowRate: 5.0,
      detectors: ['UV', 'DAD'],
      columns: ['C18', 'C8', 'Phenyl']
    },
    endpoint: 'http://localhost:8001/hplc'
  },
  {
    id: 'gcms-001',
    name: 'GC-MS System',
    type: 'gc-ms',
    category: 'analytical',
    status: 'online',
    capabilities: ['EI Ionization', 'CI Ionization', 'SIM Mode', 'Scan Mode', 'Temperature Programming'],
    parameters: {
      maxTemp: 400,
      injectionModes: ['Split', 'Splitless', 'On-column'],
      detectors: ['MS', 'FID', 'TCD'],
      massRange: '1-1000 m/z'
    },
    endpoint: 'http://localhost:8002/gcms'
  },
  {
    id: 'liquidhandler-001',
    name: 'Automated Liquid Handler',
    type: 'liquid-handler',
    category: 'preparative',
    status: 'online',
    capabilities: ['Multi-channel Pipetting', 'Plate Handling', 'Tip Washing', 'Serial Dilution'],
    parameters: {
      channels: 8,
      volumeRange: '0.5-1000µL',
      accuracy: '±1%',
      precision: '±0.5%'
    },
    endpoint: 'http://localhost:8003/liquidhandler'
  },
  {
    id: 'balance-001',
    name: 'Analytical Balance',
    type: 'balance',
    category: 'preparative',
    status: 'online',
    capabilities: ['Precision Weighing', 'Density Determination', 'Statistics'],
    parameters: {
      capacity: '220g',
      readability: '0.1mg',
      repeatability: '0.1mg',
      linearity: '±0.2mg'
    },
    endpoint: 'http://localhost:8004/balance'
  },
  {
    id: 'storage-001',
    name: 'Sample Storage System',
    type: 'storage',
    category: 'storage',
    status: 'online',
    capabilities: ['Temperature Control', 'Barcode Scanning', 'Inventory Tracking', 'Access Control'],
    parameters: {
      tempRange: '-80°C to +60°C',
      capacity: '10000 vials',
      zones: ['Freezer', 'Refrigerator', 'Ambient'],
      tracking: 'RFID + Barcode'
    },
    endpoint: 'http://localhost:8005/storage'
  },
  {
    id: 'dataprocessor-001',
    name: 'Data Processing Server',
    type: 'data-processor',
    category: 'processing',
    status: 'online',
    capabilities: ['Chromatography Analysis', 'Statistical Processing', 'Report Generation', 'Data Mining'],
    parameters: {
      algorithms: ['Peak Integration', 'Calibration', 'Quantification'],
      formats: ['CSV', 'PDF', 'XML', 'JSON'],
      storage: 'Network Attached Storage'
    },
    endpoint: 'http://localhost:8006/dataprocessor'
  }
];

export const simulatedTasks: SimulatedTask[] = [
  {
    id: 'task-sample-prep',
    name: 'Sample Preparation',
    type: 'preparation',
    instrumentType: 'liquid-handler',
    duration: 300, // 5 minutes
    parameters: {
      dilutionFactor: 10,
      solvent: 'methanol',
      volume: '1mL'
    },
    sampleInputs: ['raw-sample'],
    sampleOutputs: ['prepared-sample']
  },
  {
    id: 'task-hplc-analysis',
    name: 'HPLC Analysis',
    type: 'analysis',
    instrumentType: 'hplc',
    duration: 1800, // 30 minutes
    parameters: {
      method: 'gradient_method_1',
      injectionVolume: '10µL',
      columnTemp: '30°C',
      flowRate: '1.0mL/min'
    },
    sampleInputs: ['prepared-sample'],
    sampleOutputs: ['hplc-data']
  },
  {
    id: 'task-gcms-analysis',
    name: 'GC-MS Analysis',
    type: 'analysis',
    instrumentType: 'gc-ms',
    duration: 2400, // 40 minutes
    parameters: {
      method: 'volatiles_screening',
      injectionMode: 'splitless',
      ovenProgram: '40°C-300°C',
      scanRange: '50-500 m/z'
    },
    sampleInputs: ['prepared-sample'],
    sampleOutputs: ['gcms-data']
  },
  {
    id: 'task-weighing',
    name: 'Precise Weighing',
    type: 'preparation',
    instrumentType: 'balance',
    duration: 180, // 3 minutes
    parameters: {
      targetWeight: '100mg',
      tolerance: '±1mg',
      substance: 'reference-standard'
    },
    sampleInputs: ['bulk-material'],
    sampleOutputs: ['weighed-sample']
  },
  {
    id: 'task-storage',
    name: 'Sample Storage',
    type: 'storage',
    instrumentType: 'storage',
    duration: 60, // 1 minute
    parameters: {
      temperature: '4°C',
      location: 'refrigerator-zone',
      duration: '24h'
    },
    sampleInputs: ['processed-sample'],
    sampleOutputs: ['stored-sample']
  },
  {
    id: 'task-data-processing',
    name: 'Data Analysis',
    type: 'processing',
    instrumentType: 'data-processor',
    duration: 600, // 10 minutes
    parameters: {
      algorithm: 'peak_integration',
      calibration: 'external_standard',
      reportFormat: 'PDF'
    },
    sampleInputs: ['raw-data'],
    sampleOutputs: ['analysis-report']
  }
];

export const workflowTemplates = [
  {
    id: 'pharmaceutical-analysis',
    name: 'Pharmaceutical Analysis Workflow',
    description: 'Complete workflow for pharmaceutical sample analysis including preparation, HPLC analysis, and reporting',
    tasks: [
      'task-sample-prep',
      'task-hplc-analysis',
      'task-data-processing'
    ],
    estimatedDuration: 2700, // 45 minutes
    sampleTypes: ['tablets', 'capsules', 'solutions']
  },
  {
    id: 'environmental-screening',
    name: 'Environmental Screening',
    description: 'Environmental sample screening using GC-MS for volatile compounds',
    tasks: [
      'task-sample-prep',
      'task-gcms-analysis',
      'task-data-processing'
    ],
    estimatedDuration: 3300, // 55 minutes
    sampleTypes: ['water', 'soil', 'air']
  },
  {
    id: 'qc-testing',
    name: 'Quality Control Testing',
    description: 'Standard QC workflow with weighing, analysis, and storage',
    tasks: [
      'task-weighing',
      'task-sample-prep',
      'task-hplc-analysis',
      'task-data-processing',
      'task-storage'
    ],
    estimatedDuration: 3240, // 54 minutes
    sampleTypes: ['reference-standards', 'samples']
  }
];

// Simulation utilities
export const simulateTaskExecution = (taskId: string): Promise<any> => {
  const task = simulatedTasks.find(t => t.id === taskId);
  if (!task) {
    return Promise.reject(new Error(`Task ${taskId} not found`));
  }

  return new Promise((resolve) => {
    // Simulate task execution with progress updates
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      console.log(`Task ${task.name}: ${progress}% complete`);
      
      if (progress >= 100) {
        clearInterval(interval);
        resolve({
          taskId,
          status: 'completed',
          results: {
            executionTime: task.duration,
            outputs: task.sampleOutputs,
            data: generateMockData(task.type)
          }
        });
      }
    }, task.duration * 10); // Update every 10% of total duration
  });
};

const generateMockData = (taskType: string) => {
  switch (taskType) {
    case 'analysis':
      return {
        peaks: Math.floor(Math.random() * 10) + 5,
        purity: Math.random() * 10 + 90, // 90-100%
        retention_time: Math.random() * 20 + 5, // 5-25 minutes
        area_counts: Math.floor(Math.random() * 1000000) + 100000
      };
    case 'preparation':
      return {
        final_volume: '1.0mL',
        dilution_achieved: '10x',
        recovery: Math.random() * 5 + 95 // 95-100%
      };
    case 'storage':
      return {
        location: 'R1-S2-P15',
        barcode: `BC${Math.floor(Math.random() * 1000000)}`,
        timestamp: new Date().toISOString()
      };
    case 'processing':
      return {
        peaks_identified: Math.floor(Math.random() * 15) + 5,
        quantified_compounds: Math.floor(Math.random() * 8) + 2,
        report_pages: Math.floor(Math.random() * 10) + 5
      };
    default:
      return {};
  }
};

export const getInstrumentByType = (type: string): SimulatedInstrument | undefined => {
  return simulatedInstruments.find(instrument => instrument.type === type);
};

export const getTaskById = (id: string): SimulatedTask | undefined => {
  return simulatedTasks.find(task => task.id === id);
};