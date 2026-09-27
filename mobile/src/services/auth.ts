import { api } from './api';
import { tokenStorage } from './storage';
import {
  UserLogin,
  UserRegister,
  TokenResponse,
  RefreshTokenResponse,
  LogoutResponse,
  AuthUser,
} from '../types/auth';

export const authService = {
  async register(payload: UserRegister): Promise<TokenResponse> {
    const data = await api.post<TokenResponse>('/api/v1/auth/register', payload);
    if (data.access_token) {
      await tokenStorage.setAccessToken(data.access_token);
      await tokenStorage.setRefreshToken(data.refresh_token);
    }
    return data;
  },

  async login(payload: UserLogin): Promise<TokenResponse> {
    const data = await api.post<TokenResponse>('/api/v1/auth/login', payload);
    if (data.access_token) {
      await tokenStorage.setAccessToken(data.access_token);
      await tokenStorage.setRefreshToken(data.refresh_token);
    }
    return data;
  },

  async refresh(refreshToken: string): Promise<RefreshTokenResponse> {
    const data = await api.post<RefreshTokenResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    if (data.access_token) {
      await tokenStorage.setAccessToken(data.access_token);
    }
    return data;
  },

  async logout(): Promise<LogoutResponse> {
    const refreshToken = await tokenStorage.getRefreshToken();
    try {
      const data = await api.post<LogoutResponse>('/api/v1/auth/logout', {
        refresh_token: refreshToken || undefined,
      });
      return data;
    } finally {
      await tokenStorage.clearTokens();
    }
  },

  async getMe(): Promise<AuthUser> {
    return api.get<AuthUser>('/api/v1/auth/me');
  },
};
