import { useState, useEffect, useCallback } from 'react';
import { DeviceEventEmitter } from 'react-native';
import {
  PersonalProfileResponse,
  ProfileVisibilitySettings,
  ProfileVisibilityUpdate,
  ProgressCurvePoint,
} from '../types/profile';
import { profileService } from '../services/profile';

export function useProfile() {
  const [profile, setProfile] = useState<PersonalProfileResponse | null>(null);
  const [curve, setCurve] = useState<ProgressCurvePoint[]>([]);
  const [visibility, setVisibility] = useState<ProfileVisibilitySettings | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfileData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [profileData, curveData, visData] = await Promise.all([
        profileService.getMyProfile(),
        profileService.getCurve(14),
        profileService.getVisibility(),
      ]);
      setProfile(profileData);
      setCurve(curveData);
      setVisibility(visData);
    } catch (err: any) {
      setError(err.message || 'Failed to load profile data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfileData();
  }, [fetchProfileData]);

  // Synchronize profile and curve when a check-in is recorded
  useEffect(() => {
    const subscription = DeviceEventEmitter.addListener('focusloop:checkin_recorded', () => {
      fetchProfileData();
    });
    return () => {
      subscription.remove();
    };
  }, [fetchProfileData]);


  const updateVisibility = async (update: ProfileVisibilityUpdate) => {
    const updated = await profileService.updateVisibility(update);
    setVisibility(updated);
    if (profile) {
      setProfile({
        ...profile,
        visibility_settings: updated,
      });
    }
  };

  return {
    profile,
    curve,
    visibility,
    isLoading,
    error,
    refreshProfile: fetchProfileData,
    updateVisibility,
  };
}
