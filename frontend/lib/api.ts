import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { APP_CONFIG } from '@/config/constants';

// Create base Axios instance (calls relative /api/v1 so Next.js proxy rewrite routes it or directly to backend)
export const apiClient: AxiosInstance = axios.create({
  baseURL: typeof window !== 'undefined' ? '/api/v1' : APP_CONFIG.apiBaseUrl,
  timeout: 8000,
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
 * If backend is reachable, returns real data (unpacking StandardResponse if present).
 * If backend is unreachable or manual demo mode is active, returns mock fallback.
 */
export async function smartFetch<T>(
  requestFn: () => Promise<AxiosResponse<any>>,
  mockFallback: T | (() => T)
): Promise<T> {
  const isDemoOverride = typeof window !== 'undefined' && localStorage.getItem('maritime_demo_mode') === 'true';
  if (isDemoOverride) {
    return typeof mockFallback === 'function' ? (mockFallback as () => T)() : mockFallback;
  }

  try {
    const response = await requestFn();
    // Check if response is wrapped in StandardResponse { success: true, data: ... }
    if (response.data && typeof response.data === 'object' && 'data' in response.data) {
      return response.data.data as T;
    }
    return response.data as T;
  } catch (err) {
    return typeof mockFallback === 'function' ? (mockFallback as () => T)() : mockFallback;
  }
}
