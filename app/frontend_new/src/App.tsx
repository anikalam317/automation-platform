// TODO: Copy content from artifacts
// src/App.tsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from '@/components/Layout/Layout';
import Dashboard from '@/pages/Dashboard';
import WorkflowBuilder from '@/pages/WorkflowBuilder';
import WorkflowList from '@/pages/WorkflowList';
import WorkflowDetail from '@/pages/WorkflowDetail';
import Instruments from '@/pages/Instruments';
import Samples from '@/pages/Samples';
import Protocols from '@/pages/Protocols';
import Analytics from '@/pages/Analytics';
import Settings from '@/pages/Settings';
import '@/styles/globals.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Layout>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/workflows" element={<WorkflowList />} />
              <Route path="/workflows/new" element={<WorkflowBuilder />} />
              <Route path="/workflows/:id" element={<WorkflowDetail />} />
              <Route path="/workflows/:id/edit" element={<WorkflowBuilder />} />
              <Route path="/instruments" element={<Instruments />} />
              <Route path="/samples" element={<Samples />} />
              <Route path="/protocols" element={<Protocols />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;