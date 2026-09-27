import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const ACCESS_TOKEN_KEY = 'focusloop_access_token';
const REFRESH_TOKEN_KEY = 'focusloop_refresh_token';
const USER_KEY = 'focusloop_user';

// In-memory fallback for environments without SecureStore (e.g. some web configs)
const memoryStorage: Record<string, string> = {};

async function isSecureStoreAvailable(): Promise<boolean> {
  if (Platform.OS === 'web') {
    return false;
  }
  try {
    return await SecureStore.isAvailableAsync();
  } catch {
    return false;
  }
}

export const tokenStorage = {
  async getAccessToken(): Promise<string | null> {
    try {
      if (await isSecureStoreAvailable()) {
        return await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
      }
      if (typeof window !== 'undefined' && window.localStorage) {
        return window.localStorage.getItem(ACCESS_TOKEN_KEY);
      }
      return memoryStorage[ACCESS_TOKEN_KEY] || null;
    } catch {
      return memoryStorage[ACCESS_TOKEN_KEY] || null;
    }
  },

  async setAccessToken(token: string): Promise<void> {
    try {
      if (await isSecureStoreAvailable()) {
        await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, token);
      } else if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
      }
      memoryStorage[ACCESS_TOKEN_KEY] = token;
    } catch {
      memoryStorage[ACCESS_TOKEN_KEY] = token;
    }
  },

  async getRefreshToken(): Promise<string | null> {
    try {
      if (await isSecureStoreAvailable()) {
        return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
      }
      if (typeof window !== 'undefined' && window.localStorage) {
        return window.localStorage.getItem(REFRESH_TOKEN_KEY);
      }
      return memoryStorage[REFRESH_TOKEN_KEY] || null;
    } catch {
      return memoryStorage[REFRESH_TOKEN_KEY] || null;
    }
  },

  async setRefreshToken(token: string): Promise<void> {
    try {
      if (await isSecureStoreAvailable()) {
        await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, token);
      } else if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(REFRESH_TOKEN_KEY, token);
      }
      memoryStorage[REFRESH_TOKEN_KEY] = token;
    } catch {
      memoryStorage[REFRESH_TOKEN_KEY] = token;
    }
  },

  async clearTokens(): Promise<void> {
    try {
      if (await isSecureStoreAvailable()) {
        await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
        await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
        await SecureStore.deleteItemAsync(USER_KEY);
      }
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.removeItem(ACCESS_TOKEN_KEY);
        window.localStorage.removeItem(REFRESH_TOKEN_KEY);
        window.localStorage.removeItem(USER_KEY);
      }
      delete memoryStorage[ACCESS_TOKEN_KEY];
      delete memoryStorage[REFRESH_TOKEN_KEY];
      delete memoryStorage[USER_KEY];
    } catch {
      delete memoryStorage[ACCESS_TOKEN_KEY];
      delete memoryStorage[REFRESH_TOKEN_KEY];
      delete memoryStorage[USER_KEY];
    }
  },
};
