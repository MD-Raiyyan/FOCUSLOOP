import { api } from './api';
import {
  OnboardingStatus,
  OnboardingData,
  OnboardingUpdatePayload,
  OnboardingCompleteResponse,
} from '../types/onboarding';

export const onboardingService = {
  async getStatus(): Promise<OnboardingStatus> {
    return api.get<OnboardingStatus>('/api/v1/onboarding/status');
  },

  async getData(): Promise<OnboardingData> {
    return api.get<OnboardingData>('/api/v1/onboarding');
  },

  async saveProgress(payload: OnboardingUpdatePayload): Promise<OnboardingData> {
    return api.put<OnboardingData>('/api/v1/onboarding', payload);
  },

  async complete(): Promise<OnboardingCompleteResponse> {
    return api.post<OnboardingCompleteResponse>('/api/v1/onboarding/complete');
  },
};
