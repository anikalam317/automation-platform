# Laboratory Automation Platform Frontend

A modern React-based frontend for laboratory workflow automation with visual drag-and-drop workflow building capabilities using Drawflow.

## Features

- 🧪 **Visual Workflow Builder**: Drag-and-drop interface for creating laboratory workflows
- 📊 **Real-time Dashboard**: Monitor active workflows, instruments, and samples
- 🔬 **Instrument Management**: Track instrument status, calibration, and maintenance
- 📋 **Sample Tracking**: Comprehensive sample lifecycle management
- 📈 **Analytics**: Workflow performance and instrument utilization analytics
- 🔄 **Node-RED Integration**: Export workflows to Node-RED for execution
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🎨 **Modern UI**: Clean, intuitive interface built with Tailwind CSS

## Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Drawflow** for visual workflow creation
- **React Query** for data fetching and caching
- **React Router** for navigation
- **Recharts** for data visualization
- **Lucide React** for icons
- **React Hook Form** for form handling

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── Layout/          # Layout components
│   └── WorkflowBuilder/ # Workflow builder components
├── pages/               # Page components
├── lib/                 # Utilities and API client
├── types/               # TypeScript type definitions
├── styles/              # Global styles
└── hooks/               # Custom React hooks
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on port 5000 (or configure VITE_API_URL)

### Installation

1. Navigate to the frontend directory:
```bash
cd app/frontend_new
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local` and configure:
```env
VITE_API_URL=http://localhost:5000/api
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3001`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Integration with Existing Backend

This frontend is designed to integrate seamlessly with the existing Flask backend:

### API Endpoints Used

- `GET /api/workflows` - Fetch all workflows
- `POST /api/workflows` - Create new workflow
- `GET /api/workflows/:id` - Fetch specific workflow
- `PUT /api/workflows/:id` - Update workflow
- `DELETE /api/workflows/:id` - Delete workflow
- `POST /api/workflows/:id/start` - Start workflow execution
- `GET /api/instruments` - Fetch all instruments
- `GET /api/samples` - Fetch all samples
- `GET /api/dashboard/stats` - Dashboard statistics

### Data Models

The frontend uses TypeScript interfaces that match the backend SQLAlchemy models:

- `Workflow` - Maps to backend Workflow model
- `Task` - Maps to backend Task model  
- `Result` - Maps to backend Result model
- `Instrument` - Extended model for instrument management
- `Sample` - Model for sample tracking

## Workflow Builder

The visual workflow builder uses Drawflow to provide:

### Node Types

1. **Sample Preparation** 🧪 - Sample prep operations
2. **Analysis** 📊 - Analytical measurements
3. **Incubation** 🌡️ - Temperature/time-controlled processes
4. **Measurement** 📏 - Data collection operations
5. **Quality Control** ✓ - QC checks and validations
6. **Data Export** 💾 - Data output and reporting

### Features

- **Drag & Drop**: Intuitive node placement
- **Visual Connections**: Connect nodes to define workflow sequence
- **Parameter Configuration**: Set parameters for each operation
- **Instrument Assignment**: Assign specific instruments to tasks
- **Validation**: Real-time workflow validation
- **Simulation**: Test workflows before execution
- **Export/Import**: Save and load workflow definitions

## Node-RED Integration

Workflows created in the visual builder can be exported to Node-RED format for execution:

1. **Visual Design**: Create workflow using drag-and-drop interface
2. **Parameter Configuration**: Set operational parameters
3. **Export**: Convert to Node-RED flow format
4. **Deploy**: Send to Node-RED for execution
5. **Monitor**: Track execution through dashboard

## Customization

### Adding New Node Types

1. Define node template in `DrawflowWrapper.tsx`:
```typescript
const nodeTemplates = {
  new_operation: {
    name: 'New Operation',
    color: '#your-color',
    icon: '🔬',
    inputs: 1,
    outputs: 1,
    defaultParams: { param1: 'value1' }
  }
};
```

2. Add styling in `globals.css`:
```css
.lab-node-new_operation .node-header {
  --node-color: #your-color;
}
```

### Theming

The application supports dark mode and uses CSS custom properties for theming. Modify colors in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: { /* your color palette */ },
      lab: { /* lab-specific colors */ }
    }
  }
}
```

## Contributing

1. Follow the existing code structure and naming conventions
2. Add TypeScript types for new features
3. Include proper error handling and loading states
4. Test responsive design on multiple screen sizes
5. Update documentation for new features

## Environment Variables

- `VITE_API_URL` - Backend API base URL (default: `/api`)
- `VITE_NODE_RED_URL` - Node-RED instance URL (optional)
- `VITE_ENV` - Environment (development/production)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

This project is part of the Laboratory Automation Framework and follows the same license as the main project.

## Support

For issues related to the frontend:
1. Check the browser console for errors
2. Verify API connectivity
3. Check network requests in browser dev tools
4. Review component props and state in React dev tools

For backend integration issues, refer to the main project documentation.