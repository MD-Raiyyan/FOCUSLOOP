import { api } from './api';
import {
  PersonalProfileResponse,
  ProfileVisibilitySettings,
  ProfileVisibilityUpdate,
  ProgressCurvePoint,
  SocialProfileResponse,
} from '../types/profile';

export const profileService = {
  async getMyProfile(): Promise<PersonalProfileResponse> {
    return api.get<PersonalProfileResponse>('/api/v1/profile/me');
  },

  async getVisibility(): Promise<ProfileVisibilitySettings> {
    return api.get<ProfileVisibilitySettings>('/api/v1/profile/visibility');
  },

  async updateVisibility(
    payload: ProfileVisibilityUpdate
  ): Promise<ProfileVisibilitySettings> {
    return api.patch<ProfileVisibilitySettings>('/api/v1/profile/visibility', payload);
  },

  async getCurve(days = 14): Promise<ProgressCurvePoint[]> {
    return api.get<ProgressCurvePoint[]>(`/api/v1/profile/curve?days=${days}`);
  },

  async getUserProfile(userId: string): Promise<SocialProfileResponse> {
    return api.get<SocialProfileResponse>(`/api/v1/profile/users/${userId}`);
  },
};
