# Laboratory Automation Framework - Frontend

A modern, professional frontend for the Laboratory Automation Framework (LAF) built with React, TypeScript, and Material-UI.

## Features

### 🔬 Drag & Drop Workflow Builder
- Node-RED style visual workflow editor
- Pre-configured instrument and task nodes
- Real-time connection validation
- Visual workflow representation

### 🤖 AI-Powered Workflow Generation
- Generate workflows from natural language descriptions
- Intelligent task sequencing
- Automated parameter suggestion
- Smart instrument selection

### 📊 Real-time Monitoring Dashboard
- Live workflow execution tracking
- Task status updates via WebSocket
- Progress visualization
- Results and data display

### ⚙️ Instrument Management
- Configure laboratory instruments
- Test connections
- Manage capabilities and parameters
- Simulate instrument behavior for testing

### 🔄 Event-Driven Architecture
- WebSocket integration for real-time updates
- Automatic status synchronization
- Background task monitoring
- Live notifications

## Technology Stack

- **React 18** - Modern UI framework
- **TypeScript** - Type-safe development
- **Material-UI** - Professional UI components
- **React Flow** - Node-based workflow editor
- **Zustand** - Lightweight state management
- **React Query** - Server state management
- **Socket.IO** - Real-time communication
- **Axios** - HTTP client
- **Vite** - Fast development build tool

## Getting Started

### Prerequisites
- Node.js 16+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. Clone the repository:
\`\`\`bash
git clone <repository-url>
cd Frontend_New
\`\`\`

2. Install dependencies:
\`\`\`bash
npm install
\`\`\`

3. Set up environment variables:
\`\`\`bash
cp .env.example .env
\`\`\`

4. Start the development server:
\`\`\`bash
npm run dev
\`\`\`

The application will be available at http://localhost:3000

### Building for Production

\`\`\`bash
npm run build
\`\`\`

## Project Structure

\`\`\`
src/
├── components/          # Reusable UI components
│   ├── WorkflowNode.tsx    # Custom workflow nodes
│   ├── NodePalette.tsx     # Drag & drop component palette
│   └── AIWorkflowGenerator.tsx # AI workflow generation
├── pages/               # Main application pages
│   ├── WorkflowBuilder.tsx  # Visual workflow editor
│   ├── WorkflowMonitor.tsx  # Real-time monitoring
│   ├── WorkflowList.tsx     # Workflow management
│   └── InstrumentManager.tsx # Instrument configuration
├── services/            # API and external services
│   ├── api.ts              # HTTP API client
│   └── websocket.ts        # WebSocket service
├── store/               # State management
│   └── workflowStore.ts    # Zustand store
├── types/               # TypeScript definitions
│   └── workflow.ts         # Data models
└── utils/               # Utility functions
\`\`\`

## Key Features

### Workflow Builder
- Drag and drop interface similar to Node-RED
- Visual node connections
- Real-time validation
- Parameter configuration
- AI-assisted workflow generation

### Monitoring Dashboard
- Live execution tracking
- Progress indicators
- Task status visualization
- Results display
- Error handling and alerts

### Instrument Management
- Connection testing
- Parameter configuration
- Capability management
- Simulation mode for testing

## API Integration

The frontend integrates with the FastAPI backend through:
- RESTful API endpoints for CRUD operations
- WebSocket connections for real-time updates
- Event-driven architecture for status monitoring

## Development

### Running Tests
\`\`\`bash
npm run test
\`\`\`

### Linting
\`\`\`bash
npm run lint
\`\`\`

### Type Checking
\`\`\`bash
npm run type-check
\`\`\`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.