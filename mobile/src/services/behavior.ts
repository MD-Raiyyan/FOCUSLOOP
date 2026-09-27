import { api } from './api';
import {
  BehaviorSummary,
  PatternResponse,
  BehaviorProfileResponse,
} from '../types/behavior';

export const behaviorService = {
  async getSummary(date?: string): Promise<BehaviorSummary> {
    const url = date ? `/api/v1/behavior/summary?date=${encodeURIComponent(date)}` : '/api/v1/behavior/summary';
    return api.get<BehaviorSummary>(url);
  },

  async getPatterns(): Promise<PatternResponse[]> {
    return api.get<PatternResponse[]>('/api/v1/behavior/patterns');
  },

  async getProfile(): Promise<BehaviorProfileResponse> {
    return api.get<BehaviorProfileResponse>('/api/v1/behavior/profile');
  },

  async refresh(): Promise<{ message: string }> {
    return api.post<{ message: string }>('/api/v1/behavior/refresh');
  },
};
