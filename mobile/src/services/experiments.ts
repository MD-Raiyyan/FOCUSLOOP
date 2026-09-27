import { api } from './api';
import {
  ExperimentCreate,
  ExperimentResponse,
  ExperimentResultResponse,
  ExperimentUpdate,
} from '../types/experiments';

export const experimentService = {
  async getExperiments(): Promise<ExperimentResponse[]> {
    return api.get<ExperimentResponse[]>('/api/v1/experiments');
  },

  async createExperiment(payload: ExperimentCreate): Promise<ExperimentResponse> {
    return api.post<ExperimentResponse>('/api/v1/experiments', payload);
  },

  async suggestExperiment(): Promise<ExperimentResponse[]> {
    return api.post<ExperimentResponse[]>('/api/v1/experiments/suggest');
  },

  async evaluateExperiment(id: string): Promise<ExperimentResultResponse> {
    return api.post<ExperimentResultResponse>(
      `/api/v1/experiments/${id}/evaluate`,
      { experiment_id: id }
    );
  },

  async updateExperiment(
    id: string,
    payload: ExperimentUpdate
  ): Promise<ExperimentResponse> {
    return api.put<ExperimentResponse>(`/api/v1/experiments/${id}`, payload);
  },
};
