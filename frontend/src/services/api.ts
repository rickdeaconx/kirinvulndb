import axios from 'axios';
import { Vulnerability, AITool, Alert, VulnerabilityStats, AlertStats, PaginatedResponse } from '../types';

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth tokens (if needed)
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Vulnerability API
export const vulnerabilityApi = {
  // Get latest vulnerabilities
  getLatest: (params: {
    hours?: number;
    severity?: string;
    tool?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<PaginatedResponse<Vulnerability>> =>
    api.get('/vulnerabilities/latest', { params }).then(res => res.data),

  // Get critical vulnerabilities
  getCritical: (params: {
    unpatched_only?: boolean;
    limit?: number;
    offset?: number;
  } = {}): Promise<PaginatedResponse<Vulnerability>> =>
    api.get('/vulnerabilities/critical', { params }).then(res => res.data),

  // Get vulnerabilities by tool
  getByTool: (
    toolName: string,
    params: {
      severity?: string;
      patch_status?: string;
      limit?: number;
      offset?: number;
    } = {}
  ): Promise<PaginatedResponse<Vulnerability>> =>
    api.get(`/vulnerabilities/by-tool/${toolName}`, { params }).then(res => res.data),

  // Search vulnerabilities
  search: (params: {
    q: string;
    severity?: string;
    tool?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<Vulnerability>> =>
    api.get('/vulnerabilities/search', { params }).then(res => res.data),

  // Get trending vulnerabilities
  getTrending: (days: number = 7): Promise<{ trending_vulnerabilities: Vulnerability[]; period_days: number; count: number }> =>
    api.get('/vulnerabilities/trending', { params: { days } }).then(res => res.data),

  // Get vulnerability statistics
  getStats: (days: number = 30): Promise<VulnerabilityStats> =>
    api.get('/vulnerabilities/stats', { params: { days } }).then(res => res.data),

  // Get specific vulnerability
  getById: (vulnerabilityId: string): Promise<Vulnerability> =>
    api.get(`/vulnerabilities/${vulnerabilityId}`).then(res => res.data),
};

// Tools API
export const toolsApi = {
  // Get all tools
  getAll: (params: {
    active_only?: boolean;
    limit?: number;
    offset?: number;
  } = {}): Promise<PaginatedResponse<AITool>> =>
    api.get('/tools', { params }).then(res => res.data),

  // Get specific tool
  getByName: (toolName: string): Promise<AITool> =>
    api.get(`/tools/${toolName}`).then(res => res.data),

  // Get tool vulnerabilities
  getVulnerabilities: (
    toolName: string,
    params: {
      limit?: number;
      offset?: number;
    } = {}
  ): Promise<{ tool: string; vulnerabilities: Vulnerability[]; total: number; limit: number; offset: number }> =>
    api.get(`/tools/${toolName}/vulnerabilities`, { params }).then(res => res.data),
};

// Alerts API
export const alertsApi = {
  // Get all alerts
  getAll: (params: {
    status?: string;
    priority?: string;
    alert_type?: string;
    hours?: number;
    limit?: number;
    offset?: number;
  } = {}): Promise<PaginatedResponse<Alert>> =>
    api.get('/alerts', { params }).then(res => res.data),

  // Get critical alerts
  getCritical: (params: {
    pending_only?: boolean;
    limit?: number;
    offset?: number;
  } = {}): Promise<PaginatedResponse<Alert>> =>
    api.get('/alerts/critical', { params }).then(res => res.data),

  // Get alert statistics
  getStats: (days: number = 7): Promise<AlertStats> =>
    api.get('/alerts/stats', { params: { days } }).then(res => res.data),

  // Get specific alert
  getById: (alertId: string): Promise<Alert> =>
    api.get(`/alerts/${alertId}`).then(res => res.data),

  // Acknowledge alert
  acknowledge: (alertId: string): Promise<{ message: string }> =>
    api.post(`/alerts/${alertId}/acknowledge`).then(res => res.data),

  // Resolve alert
  resolve: (alertId: string): Promise<{ message: string }> =>
    api.post(`/alerts/${alertId}/resolve`).then(res => res.data),
};

// Health API
export const healthApi = {
  // Basic health check
  check: (): Promise<{ status: string; timestamp: string; service: string; version: string }> =>
    api.get('/health').then(res => res.data),

  // Detailed health check
  detailed: (): Promise<any> =>
    api.get('/health/detailed').then(res => res.data),

  // Get metrics
  metrics: (): Promise<any> =>
    api.get('/health/metrics').then(res => res.data),
};

export default api;