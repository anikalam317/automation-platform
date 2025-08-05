// TODO: Copy content from artifacts
// src/pages/Dashboard.tsx

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity,
  Clock,
  FlaskConical,
  TestTube,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  BarChart3,
  XCircle,
  Pause,
  Play,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import apiClient from '@/lib/api';
import type { Workflow, Instrument } from '@/types';

const Dashboard: React.FC = () => {
  // Fetch dashboard data
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.getDashboardStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: workflows } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => apiClient.getWorkflows(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const { data: instruments } = useQuery({
    queryKey: ['instruments'],
    queryFn: () => apiClient.getInstruments(),
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  const { data: analytics } = useQuery({
    queryKey: ['workflow-analytics'],
    queryFn: () => apiClient.getWorkflowAnalytics('7d'),
  });

  // Calculate derived data
  const recentWorkflows = workflows?.slice(0, 5) || [];
  const activeWorkflows = workflows?.filter(w => w.status === 'running') || [];
  const completedToday = workflows?.filter(w => 
    w.status === 'completed' && 
    new Date(w.updated_at).toDateString() === new Date().toDateString()
  ) || [];

  const instrumentsByStatus = instruments?.reduce((acc, instrument) => {
    acc[instrument.status] = (acc[instrument.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const statsCards = [
    {
      title: 'Active Workflows',
      value: stats?.active_workflows || activeWorkflows.length,
      icon: Activity,
      color: 'bg-blue-500',
      change: '+12%',
      changeType: 'positive',
    },
    {
      title: 'Completed Today',
      value: stats?.completed_today || completedToday.length,
      icon: CheckCircle,
      color: 'bg-green-500',
      change: '+8%',
      changeType: 'positive',
    },
    {
      title: 'Busy Instruments',
      value: stats?.instruments_busy || instrumentsByStatus.busy || 0,
      icon: FlaskConical,
      color: 'bg-orange-500',
      change: '-2%',
      changeType: 'negative',
    },
    {
      title: 'Samples Processed',
      value: stats?.samples_processed || 0,
      icon: TestTube,
      color: 'bg-purple-500',
      change: '+15%',
      changeType: 'positive',
    },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Laboratory Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Monitor your laboratory automation workflows and instrument status
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statsCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.title} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className={`flex-shrink-0 ${stat.color} rounded-md p-3`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.title}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900">
                        {stat.value}
                      </div>
                      <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                        stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        <TrendingUp className="h-4 w-4 self-center flex-shrink-0" />
                        {stat.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Workflow Completion Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Workflow Completion Times (7 days)
          </h3>
          {analytics?.completion_times ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analytics.completion_times}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="average_duration" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-300 flex items-center justify-center text-gray-500">
              No data available
            </div>
          )}
        </div>

        {/* Instrument Utilization */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Instrument Utilization
          </h3>
          {analytics?.instrument_utilization ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.instrument_utilization}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="instrument" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="utilization" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-300 flex items-center justify-center text-gray-500">
              No data available
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Workflows */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Recent Workflows</h3>
              <Link
                to="/workflows"
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                View all
              </Link>
            </div>
          </div>
          <div className="divide-y divide-gray-200">
            {recentWorkflows.length > 0 ? (
              recentWorkflows.map((workflow) => (
                <div key={workflow.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      {getStatusIcon(workflow.status)}
                      <div className="ml-3">
                        <Link
                          to={`/workflows/${workflow.id}`}
                          className="text-sm font-medium text-gray-900 hover:text-blue-600"
                        >
                          {workflow.name}
                        </Link>
                        <p className="text-sm text-gray-500">
                          {workflow.tasks.length} tasks
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        getStatusColor(workflow.status)
                      }`}>
                        {workflow.status}
                      </span>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-gray-400">
                    {new Date(workflow.updated_at).toLocaleString()}
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-gray-500">
                No workflows yet
              </div>
            )}
          </div>
        </div>

        {/* Instrument Status */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Instrument Status</h3>
              <Link
                to="/instruments"
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                View all
              </Link>
            </div>
          </div>
          <div className="divide-y divide-gray-200">
            {instruments && instruments.length > 0 ? (
              instruments.slice(0, 5).map((instrument) => (
                <div key={instrument.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <FlaskConical className="h-5 w-5 text-gray-400" />
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">
                          {instrument.name}
                        </div>
                        <p className="text-sm text-gray-500">
                          {instrument.type}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        instrument.status === 'available' 
                          ? 'bg-green-100 text-green-800'
                          : instrument.status === 'busy'
                          ? 'bg-yellow-100 text-yellow-800'
                          : instrument.status === 'maintenance'
                          ? 'bg-orange-100 text-orange-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {instrument.status}
                      </span>
                    </div>
                  </div>
                  {instrument.current_task_id && (
                    <div className="mt-2 text-xs text-gray-400">
                      Running task #{instrument.current_task_id}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-gray-500">
                No instruments configured
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8 bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/workflows/new"
            className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <Activity className="h-5 w-5 mr-2 text-blue-500" />
            Create New Workflow
          </Link>
          <Link
            to="/samples"
            className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <TestTube className="h-5 w-5 mr-2 text-green-500" />
            Manage Samples
          </Link>
          <Link
            to="/analytics"
            className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <BarChart3 className="h-5 w-5 mr-2 text-purple-500" />
            View Analytics
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;