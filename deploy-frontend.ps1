# Navigate to your automation platform root directory
#cd your-automation-platform-path

# Create the main frontend directory
New-Item -ItemType Directory -Path "app\frontend_new" -Force

# Create all subdirectories
$directories = @(
    "app\frontend_new\src\components\Layout",
    "app\frontend_new\src\components\WorkflowBuilder", 
    "app\frontend_new\src\components\UI",
    "app\frontend_new\src\components\Charts",
    "app\frontend_new\src\components\Forms",
    "app\frontend_new\src\pages",
    "app\frontend_new\src\lib",
    "app\frontend_new\src\types",
    "app\frontend_new\src\styles",
    "app\frontend_new\src\hooks",
    "app\frontend_new\src\utils",
    "app\frontend_new\src\assets\images",
    "app\frontend_new\src\assets\icons",
    "app\frontend_new\public",
    "app\frontend_new\dist"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force
}

Write-Host "✅ Directory structure created successfully!" -ForegroundColor Green



# Navigate to the new frontend directory
cd app\frontend_new

# Create package.json
@'
{
  "name": "lab-automation-frontend",
  "version": "1.0.0",
  "description": "Laboratory Automation Platform Frontend with Visual Workflow Builder",
  "type": "module",
  "scripts": {
    "dev": "vite --port 3001",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview --port 3001",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.1",
    "drawflow": "^0.0.60",
    "axios": "^1.3.4",
    "recharts": "^2.5.0",
    "lucide-react": "^0.263.1",
    "@tanstack/react-query": "^4.24.6",
    "react-hook-form": "^7.43.2",
    "react-hot-toast": "^2.4.0",
    "clsx": "^1.2.1",
    "date-fns": "^2.29.3"
  },
  "devDependencies": {
    "@types/react": "^18.0.28",
    "@types/react-dom": "^18.0.11",
    "@types/node": "^18.15.0",
    "@vitejs/plugin-react": "^3.1.0",
    "typescript": "^4.9.3",
    "vite": "^4.1.0",
    "eslint": "^8.36.0",
    "@typescript-eslint/eslint-plugin": "^5.55.0",
    "@typescript-eslint/parser": "^5.55.0",
    "eslint-plugin-react": "^7.32.2",
    "eslint-plugin-react-hooks": "^4.6.0",
    "vitest": "^0.28.5",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/user-event": "^14.4.3",
    "tailwindcss": "^3.2.7",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.21"
  }
}
'@ | Out-File -FilePath "package.json" -Encoding UTF8

Write-Host "✅ package.json created" -ForegroundColor Green



# Create vite.config.ts
@'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  define: {
    'process.env': process.env,
  },
})
'@ | Out-File -FilePath "vite.config.ts" -Encoding UTF8

Write-Host "✅ vite.config.ts created" -ForegroundColor Green


# Create tsconfig.json
@'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "allowJs": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    /* Path mapping */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
'@ | Out-File -FilePath "tsconfig.json" -Encoding UTF8

# Create tsconfig.node.json
@'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
'@ | Out-File -FilePath "tsconfig.node.json" -Encoding UTF8

Write-Host "✅ TypeScript configuration created" -ForegroundColor Green



# Create tailwind.config.js
@'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe', 
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        lab: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        workflow: {
          pending: '#fbbf24',
          running: '#3b82f6',
          completed: '#10b981',
          failed: '#ef4444',
          paused: '#f59e0b',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Monaco', 'monospace'],
      },
      boxShadow: {
        'lab': '0 4px 6px -1px rgba(59, 130, 246, 0.1), 0 2px 4px -1px rgba(59, 130, 246, 0.06)',
        'workflow': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [],
}
'@ | Out-File -FilePath "tailwind.config.js" -Encoding UTF8

# Create postcss.config.js  
@'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'@ | Out-File -FilePath "postcss.config.js" -Encoding UTF8

Write-Host "✅ Tailwind configuration created" -ForegroundColor Green


# Create index.html
@'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/lab-icon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Laboratory Automation Platform - Visual Workflow Builder for Laboratory Information Management" />
    <title>Lab Automation Platform</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'@ | Out-File -FilePath "index.html" -Encoding UTF8

# Create main.tsx
New-Item -ItemType Directory -Path "src" -Force
@'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'@ | Out-File -FilePath "src\main.tsx" -Encoding UTF8

Write-Host "✅ HTML template and main files created" -ForegroundColor Green



# You'll need to create these files manually in VS Code by copying from the artifacts:
# 1. src/App.tsx
# 2. src/types/index.ts  
# 3. src/lib/api.ts
# 4. src/components/Layout/Layout.tsx
# 5. src/components/WorkflowBuilder/DrawflowWrapper.tsx
# 6. src/pages/Dashboard.tsx
# 7. src/pages/WorkflowBuilder.tsx
# 8. src/styles/globals.css

# Create placeholder files for now
$sourceFiles = @(
    "src\App.tsx",
    "src\types\index.ts",
    "src\lib\api.ts", 
    "src\components\Layout\Layout.tsx",
    "src\components\WorkflowBuilder\DrawflowWrapper.tsx",
    "src\pages\Dashboard.tsx",
    "src\pages\WorkflowBuilder.tsx",
    "src\pages\WorkflowList.tsx",
    "src\pages\WorkflowDetail.tsx",
    "src\pages\Instruments.tsx",
    "src\pages\Samples.tsx",
    "src\pages\Protocols.tsx",
    "src\pages\Analytics.tsx",
    "src\pages\Settings.tsx",
    "src\styles\globals.css"
)

foreach ($file in $sourceFiles) {
    New-Item -ItemType File -Path $file -Force
    "// TODO: Copy content from artifacts" | Out-File -FilePath $file -Encoding UTF8
}

Write-Host "✅ Source file structure created" -ForegroundColor Green



# Create .env.example
@'
# API Configuration
VITE_API_URL=http://localhost:5000/api

# Node-RED Integration (optional)
VITE_NODE_RED_URL=http://localhost:1880

# Environment
VITE_ENV=development
'@ | Out-File -FilePath ".env.example" -Encoding UTF8

# Create .env.local for development
@'
VITE_API_URL=http://localhost:5000/api
VITE_ENV=development
'@ | Out-File -FilePath ".env.local" -Encoding UTF8

Write-Host "✅ Environment configuration created" -ForegroundColor Green



# Create .gitignore
@'
# Dependencies
node_modules/
/.pnp
.pnp.js

# Production
/build
/dist

# Environment variables
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage
*.lcov

# nyc test coverage
.nyc_output

# ESLint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Vite
.vite

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
'@ | Out-File -FilePath ".gitignore" -Encoding UTF8

Write-Host "✅ .gitignore created" -ForegroundColor Green



# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "📦 Installing dependencies... This may take a few minutes." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}


Write-Host "📋 Now you need to copy the content from the artifacts:" -ForegroundColor Yellow
Write-Host ""
Write-Host "In VS Code, copy the content from each artifact to the corresponding file:" -ForegroundColor White
Write-Host "1. Copy 'Main App Component' content to src/App.tsx" -ForegroundColor Cyan
Write-Host "2. Copy 'TypeScript Type Definitions' content to src/types/index.ts" -ForegroundColor Cyan  
Write-Host "3. Copy 'API Client' content to src/lib/api.ts" -ForegroundColor Cyan
Write-Host "4. Copy 'Layout Component' content to src/components/Layout/Layout.tsx" -ForegroundColor Cyan
Write-Host "5. Copy 'Drawflow Wrapper Component' content to src/components/WorkflowBuilder/DrawflowWrapper.tsx" -ForegroundColor Cyan
Write-Host "6. Copy 'Dashboard Page' content to src/pages/Dashboard.tsx" -ForegroundColor Cyan
Write-Host "7. Copy 'Workflow Builder Page' content to src/pages/WorkflowBuilder.tsx" -ForegroundColor Cyan  
Write-Host "8. Copy 'Global CSS Styles' content to src/styles/globals.css" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Tip: Open each artifact in the chat and copy-paste the content to the corresponding file." -ForegroundColor Green



# Create simple placeholder components for other pages
@'
import React from 'react';

const WorkflowList: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Workflows</h1>
      <p>Workflow list will be implemented here.</p>
    </div>
  );
};

export default WorkflowList;
'@ | Out-File -FilePath "src\pages\WorkflowList.tsx" -Encoding UTF8

@'
import React from 'react';

const WorkflowDetail: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Workflow Detail</h1>
      <p>Workflow detail will be implemented here.</p>
    </div>
  );
};

export default WorkflowDetail;
'@ | Out-File -FilePath "src\pages\WorkflowDetail.tsx" -Encoding UTF8

# Create similar placeholders for other pages
$pages = @("Instruments", "Samples", "Protocols", "Analytics", "Settings")
foreach ($page in $pages) {
@"
import React from 'react';

const ${page}: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">${page}</h1>
      <p>${page} page will be implemented here.</p>
    </div>
  );
};

export default ${page};
"@ | Out-File -FilePath "src\pages\${page}.tsx" -Encoding UTF8
}

Write-Host "✅ Placeholder pages created" -ForegroundColor Green


