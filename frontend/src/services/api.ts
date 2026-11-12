import axios from 'axios';
import { DevUser, TokenResponse, User } from '../types/auth';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Automatically injects dev persona or bearer token
apiClient.interceptors.request.use((config) => {
  const devUser = localStorage.getItem('society_dev_user');
  const token = localStorage.getItem('society_auth_token');

  if (devUser) {
    config.headers['X-Dev-User'] = devUser;
  }
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  return config;
});

export interface HealthCheckResponse {
  status: string;
  project: string;
  environment: string;
  version: string;
}

export const fetchHealthCheck = async (): Promise<HealthCheckResponse> => {
  const response = await apiClient.get<HealthCheckResponse>('/health');
  return response.data;
};

export const fetchCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
};

export const fetchDevUsers = async (): Promise<DevUser[]> => {
  const response = await apiClient.get<DevUser[]>('/auth/dev-users');
  return response.data;
};

export const devLogin = async (email: string): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/dev-login', { email });
  return response.data;
};
