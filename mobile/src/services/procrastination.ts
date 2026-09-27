import { api } from './api';
import {
  ProcrastinationEventCreate,
  ProcrastinationEventEnd,
  ProcrastinationEventResponse,
} from '../types/procrastination';

export const procrastinationService = {
  async startEvent(
    payload?: ProcrastinationEventCreate
  ): Promise<ProcrastinationEventResponse> {
    return api.post<ProcrastinationEventResponse>(
      '/api/v1/procrastination/start',
      payload || {}
    );
  },

  async endEvent(
    eventId: string,
    payload?: ProcrastinationEventEnd
  ): Promise<ProcrastinationEventResponse> {
    return api.post<ProcrastinationEventResponse>(
      `/api/v1/procrastination/${eventId}/end`,
      payload || {}
    );
  },

  async getEvents(): Promise<ProcrastinationEventResponse[]> {
    return api.get<ProcrastinationEventResponse[]>('/api/v1/procrastination');
  },
};
