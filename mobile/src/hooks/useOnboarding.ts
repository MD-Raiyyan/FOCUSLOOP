import { useState, useEffect, useCallback } from 'react';
import { onboardingService } from '../services/onboarding';
import {
  OnboardingStatus,
  OnboardingData,
  OnboardingUpdatePayload,
} from '../types/onboarding';
import { useAuth } from '../context/AuthContext';

export function useOnboarding() {
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [data, setData] = useState<OnboardingData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await onboardingService.getStatus();
      setStatus(res);
      return res;
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch onboarding status');
      return null;
    }
  }, []);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await onboardingService.getData();
      setData(res);
      return res;
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch onboarding data');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const saveStep = async (payload: OnboardingUpdatePayload): Promise<boolean> => {
    try {
      setIsSaving(true);
      setError(null);
      const updated = await onboardingService.saveProgress(payload);
      setData(updated);
      return true;
    } catch (err: any) {
      setError(err?.message || 'Failed to save progress');
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  const completeOnboarding = async (): Promise<boolean> => {
    try {
      setIsSaving(true);
      setError(null);
      await onboardingService.complete();
      await refreshUser();
      return true;
    } catch (err: any) {
      setError(err?.message || 'Failed to complete onboarding');
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  return {
    status,
    data,
    isLoading,
    isSaving,
    error,
    fetchStatus,
    fetchData,
    saveStep,
    completeOnboarding,
  };
}
