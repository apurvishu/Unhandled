import { apiClient, smartFetch } from '@/lib/api';
import { AuthResponse, User, UserRole } from '@/types';
import { DEMO_USERS } from '@/config/constants';

export async function loginApi(email: string, password?: string): Promise<AuthResponse> {
  return smartFetch<AuthResponse>(
    () => apiClient.post('/auth/login', { email, password }),
    () => {
      const user = Object.values(DEMO_USERS).find((u) => u.email === email) || DEMO_USERS.PROCUREMENT_OFFICER;
      return {
        user,
        tokens: {
          accessToken: 'demo_access_token_' + user.role,
          refreshToken: 'demo_refresh_token_' + user.role,
          tokenType: 'Bearer',
          expiresIn: 3600,
        },
      };
    }
  );
}

export async function registerApi(data: {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  companyName?: string;
}): Promise<AuthResponse> {
  return smartFetch<AuthResponse>(
    () => apiClient.post('/auth/register', data),
    () => {
      const user: User = {
        id: 'usr-' + Date.now(),
        name: data.name,
        email: data.email,
        role: data.role,
        companyName: data.companyName || 'Maritime Partner Corp',
        createdAt: new Date().toISOString(),
      };
      return {
        user,
        tokens: {
          accessToken: 'demo_token_' + Date.now(),
          refreshToken: 'demo_refresh_' + Date.now(),
          tokenType: 'Bearer',
          expiresIn: 3600,
        },
      };
    }
  );
}

export async function getCurrentUserApi(): Promise<User> {
  return smartFetch<User>(
    () => apiClient.get('/auth/me'),
    () => DEMO_USERS.PROCUREMENT_OFFICER
  );
}
