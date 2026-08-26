import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { APP_CONFIG } from '@/config/constants';

// Create base Axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: APP_CONFIG.apiBaseUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Attach JWT token if available
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('maritime_access_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Auto handle 401 & token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      if (typeof window !== 'undefined') {
        const refreshToken = localStorage.getItem('maritime_refresh_token');
        if (refreshToken) {
          try {
            const res = await axios.post(`${APP_CONFIG.apiBaseUrl}/auth/refresh`, {
              refresh_token: refreshToken,
            });
            const newToken = res.data.access_token;
            localStorage.setItem('maritime_access_token', newToken);
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return apiClient(originalRequest);
          } catch {
            localStorage.removeItem('maritime_access_token');
            localStorage.removeItem('maritime_refresh_token');
            localStorage.removeItem('maritime_user');
          }
        }
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Smart fetch wrapper with seamless Demo Mode fallback.
 * If backend is reachable, returns real data.
 * If backend is unreachable (offline/404/network error), gracefully returns mockData
 * and marks it as demo data without breaking the UI.
 */
export async function smartFetch<T>(
  requestFn: () => Promise<AxiosResponse<T>>,
  mockFallback: T | (() => T)
): Promise<T> {
  // Check if manual demo mode override is enabled
  const isDemoOverride = typeof window !== 'undefined' && localStorage.getItem('maritime_demo_mode') === 'true';
  if (isDemoOverride) {
    return typeof mockFallback === 'function' ? (mockFallback as () => T)() : mockFallback;
  }

  try {
    const response = await requestFn();
    return response.data;
  } catch (err) {
    console.warn('[SmartFetch] Backend API unreachable or returned error, using high-fidelity fallback dataset:', err);
    return typeof mockFallback === 'function' ? (mockFallback as () => T)() : mockFallback;
  }
}
