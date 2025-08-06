import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

const DB_SERVICE_URL = import.meta.env.VITE_DB_SERVICE_URL || 'http://localhost:7000';

export interface DBServiceResponse<T> {
  message?: string;
  data?: T;
  [key: string]: any;
}

// ============================================================================
// DB SERVICE API CLIENT - Direct to DB Service
// ============================================================================

export const dbClient: AxiosInstance = axios.create({
  baseURL: DB_SERVICE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
});

dbClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Remove null fields from request
    if (config.data && typeof config.data === 'object') {
      config.data = Object.fromEntries(
        Object.entries(config.data).filter(([_, value]) => value != null)
      );
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ============================================================================
// RESPONSE INTERCEPTOR - Handle Errors
// ============================================================================

dbClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const errorMessage = error.response?.data?.message || error.response?.data?.detail || error.message || 'An error occurred';
    
    // Don't show toast for cancelled requests
    if (error.code !== 'ERR_CANCELED') {
      console.error('DB Service API Error:', errorMessage, error.response?.data);
    }

    return Promise.reject(error);
  }
);

// ============================================================================
// GENERIC REQUEST FUNCTIONS - DB Service
// ============================================================================

export const dbApi = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> =>
    dbClient.get(url, config).then(response => response.data),
    
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> =>
    dbClient.post(url, data, config).then(response => response.data),
    
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> =>
    dbClient.put(url, data, config).then(response => response.data),
    
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> =>
    dbClient.patch(url, data, config).then(response => response.data),
    
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> =>
    dbClient.delete(url, config).then(response => response.data),
};
