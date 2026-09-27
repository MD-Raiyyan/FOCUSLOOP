import { api } from './api';
import { CheckinCreate, CheckinResponse } from '../types/checkin';

export const checkinService = {
  async createCheckin(payload: CheckinCreate): Promise<CheckinResponse> {
    return api.post<CheckinResponse>('/api/v1/checkins', payload);
  },

  async getCheckins(date?: string, taskId?: string): Promise<CheckinResponse[]> {
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (taskId) params.append('task_id', taskId);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return api.get<CheckinResponse[]>(`/api/v1/checkins${queryString}`);
  },
};
