# Laboratory Automation Framework - Frontend Setup Guide

This guide will help you set up and run the new Laboratory Automation Framework frontend with all its features.

## Prerequisites

- Node.js 16+ and npm
- Python 3.8+ (for backend)
- PostgreSQL (for backend database)
- Git

## Quick Start

### 1. Setup Backend (if not already running)

```bash
# Navigate to backend directory
cd ../app/backend

# Install Python dependencies
pip install -r requirements.txt

# Setup database
# (Make sure PostgreSQL is running)
python -m laf.core.database

# Start backend server
uvicorn laf.api.main:app --reload --port 8000
```

### 2. Setup Frontend

```bash
# Navigate to Frontend_New directory
cd Frontend_New

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

### 3. Setup Instrument Simulators (Optional)

```bash
# Navigate to scripts directory
cd scripts

# Install simulator dependencies
npm install

# Start instrument simulators
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Features Overview

### 🔬 Drag & Drop Workflow Builder
Navigate to `/builder` to create workflows visually:
- Drag instrument and task nodes from the palette
- Connect nodes to create workflow sequences
- Configure parameters for each node
- Save and execute workflows

### 🤖 AI Workflow Generation
- Click "AI Generate" in the workflow builder
- Describe your workflow in natural language
- AI will generate appropriate task sequences
- Example prompts:
  - "Create a workflow for HPLC analysis of pharmaceutical samples"
  - "Design an environmental water testing workflow with GC-MS"
  - "Build a protein purification workflow"

### 📊 Real-time Monitoring
Navigate to `/monitor` to track workflow execution:
- Live status updates via WebSocket
- Progress tracking and visualization
- Task execution details
- Results and data display

### ⚙️ Instrument Management
Navigate to `/instruments` to manage laboratory instruments:
- Add and configure instruments
- Test connections
- Manage capabilities and parameters
- Simulation mode for testing

## Architecture

### Frontend Stack
- **React 18** with TypeScript
- **Material-UI** for professional UI components
- **React Flow** for drag-and-drop workflow builder
- **Zustand** for state management
- **React Query** for server state management
- **Socket.IO** for real-time communication

### Backend Integration
- RESTful API endpoints for CRUD operations
- WebSocket connections for real-time updates
- Event-driven architecture for status monitoring

## Development

### Project Structure
```
Frontend_New/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── WorkflowNode.tsx    # Custom workflow nodes
│   │   ├── NodePalette.tsx     # Component palette
│   │   └── AIWorkflowGenerator.tsx # AI workflow generation
│   ├── pages/               # Main application pages
│   │   ├── WorkflowBuilder.tsx  # Visual workflow editor
│   │   ├── WorkflowMonitor.tsx  # Real-time monitoring
│   │   ├── WorkflowList.tsx     # Workflow management
│   │   └── InstrumentManager.tsx # Instrument configuration
│   ├── services/            # API and external services
│   ├── store/               # State management
│   ├── types/               # TypeScript definitions
│   └── utils/               # Utility functions
├── scripts/                 # Instrument simulators
└── public/                  # Static assets
```

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

### Environment Variables
Create a `.env` file with:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
```

## Testing

### Using Instrument Simulators
1. Start the instrument simulators: `cd scripts && npm start`
2. Create a workflow in the builder
3. The simulators will respond to instrument tasks with mock data
4. Monitor execution in real-time

### Sample Workflows
The system includes several pre-configured workflow templates:
- Pharmaceutical Analysis
- Environmental Screening
- Quality Control Testing
- Protein Purification

## Production Deployment

### Build Frontend
```bash
npm run build
```

### Serve with Nginx (example configuration)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/Frontend_New/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /socket.io {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Troubleshooting

### Common Issues

1. **Backend not connecting**
   - Ensure backend is running on port 8000
   - Check CORS settings in backend
   - Verify API_URL in .env file

2. **WebSocket connection fails**
   - Check if backend WebSocket endpoint is accessible
   - Verify WS_URL in .env file
   - Check browser console for connection errors

3. **AI workflow generation not working**
   - Ensure backend AI endpoint is implemented
   - Check backend logs for errors
   - Verify network connectivity

4. **Instrument simulators not responding**
   - Make sure simulators are running (`cd scripts && npm start`)
   - Check that ports 8001-8005 are available
   - Verify simulator health endpoints

### Getting Help
- Check browser console for JavaScript errors
- Review backend logs for API errors
- Ensure all dependencies are installed
- Verify environment variables are set correctly

## Security Considerations

For production deployment:
- Set up proper CORS origins (not "*")
- Implement authentication and authorization
- Use HTTPS for all connections
- Secure WebSocket connections
- Validate all user inputs
- Implement rate limiting

## Performance Optimization

- Enable gzip compression
- Use CDN for static assets
- Implement caching strategies
- Optimize bundle size
- Use React.memo for expensive components
- Implement virtual scrolling for large lists

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.