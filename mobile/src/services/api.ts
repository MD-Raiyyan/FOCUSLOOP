import { tokenStorage } from './storage';
import { RefreshTokenResponse } from '../types/auth';

export const API_BASE_URL = (
  process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000'
).replace(/\/+$/, '');

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

type UnauthorizedHandler = () => void;
let unauthorizedHandler: UnauthorizedHandler | null = null;

export function setUnauthorizedHandler(handler: UnauthorizedHandler) {
  unauthorizedHandler = handler;
}

// Queue for handling concurrent 401 requests while a refresh is in flight
let isRefreshing = false;
let refreshSubscribers: Array<(token: string | null) => void> = [];

function subscribeTokenRefresh(cb: (token: string | null) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token: string | null) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  isRetry = false
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(options.headers as Record<string, string>),
  };

  const token = await tokenStorage.getAccessToken();
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  let response: Response;
  try {
    response = await fetch(url, config);
  } catch (err: any) {
    throw new ApiError(
      `Network error: Could not connect to FocusLoop server at ${API_BASE_URL}. ${err.message || ''}`,
      0
    );
  }

  // Handle 401 Unauthorized
  const isAuthEndpoint =
    endpoint.includes('/auth/login') ||
    endpoint.includes('/auth/register') ||
    endpoint.includes('/auth/refresh');

  if (response.status === 401 && !isRetry && !isAuthEndpoint) {
    if (!isRefreshing) {
      isRefreshing = true;
      const refreshToken = await tokenStorage.getRefreshToken();

      if (!refreshToken) {
        isRefreshing = false;
        await tokenStorage.clearTokens();
        if (unauthorizedHandler) unauthorizedHandler();
        throw new ApiError('Session expired. Please log in again.', 401);
      }

      try {
        const refreshResponse = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!refreshResponse.ok) {
          throw new Error('Refresh failed');
        }

        const refreshData: RefreshTokenResponse = await refreshResponse.json();
        await tokenStorage.setAccessToken(refreshData.access_token);
        isRefreshing = false;
        onRefreshed(refreshData.access_token);
      } catch (refreshErr) {
        isRefreshing = false;
        onRefreshed(null);
        await tokenStorage.clearTokens();
        if (unauthorizedHandler) unauthorizedHandler();
        throw new ApiError('Session expired. Please log in again.', 401);
      }
    }

    // Wait for the in-flight refresh to finish
    return new Promise<T>((resolve, reject) => {
      subscribeTokenRefresh(async (newToken) => {
        if (!newToken) {
          reject(new ApiError('Session expired. Please log in again.', 401));
          return;
        }

        try {
          const retriedHeaders = {
            ...headers,
            Authorization: `Bearer ${newToken}`,
          };
          const retried = await request<T>(
            endpoint,
            { ...options, headers: retriedHeaders },
            true
          );
          resolve(retried);
        } catch (retryErr) {
          reject(retryErr);
        }
      });
    });
  }

  // Handle No Content (204)
  if (response.status === 204) {
    return {} as T;
  }

  let data: any = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    if (data) {
      if (typeof data.detail === 'string') {
        errorMessage = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMessage = data.detail
          .map((d: any) => (d.msg ? `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}` : JSON.stringify(d)))
          .join(', ');
      } else if (data.message) {
        errorMessage = data.message;
      }
    }
    throw new ApiError(errorMessage, response.status, data);
  }

  return data as T;
}

export const api = {
  get<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
    return request<T>(endpoint, { method: 'GET', headers });
  },

  post<T>(endpoint: string, body?: any, headers?: Record<string, string>): Promise<T> {
    return request<T>(endpoint, {
      method: 'POST',
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },

  put<T>(endpoint: string, body?: any, headers?: Record<string, string>): Promise<T> {
    return request<T>(endpoint, {
      method: 'PUT',
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },

  patch<T>(endpoint: string, body?: any, headers?: Record<string, string>): Promise<T> {
    return request<T>(endpoint, {
      method: 'PATCH',
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },

  delete<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
    return request<T>(endpoint, { method: 'DELETE', headers });
  },
};
