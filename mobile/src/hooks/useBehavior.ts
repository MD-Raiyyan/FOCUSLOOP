import { useState, useEffect, useCallback } from 'react';
import { DeviceEventEmitter } from 'react-native';
import { BehaviorSummary, PatternResponse } from '../types/behavior';
import { behaviorService } from '../services/behavior';

export function useBehavior(date?: string) {
  const [summary, setSummary] = useState<BehaviorSummary | null>(null);
  const [patterns, setPatterns] = useState<PatternResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBehavior = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [sumData, patData] = await Promise.all([
        behaviorService.getSummary(date),
        behaviorService.getPatterns(),
      ]);
      setSummary(sumData);
      setPatterns(patData);
    } catch (err: any) {
      setError(err.message || 'Failed to load behavioral intelligence');
    } finally {
      setIsLoading(false);
    }
  }, [date]);

  useEffect(() => {
    fetchBehavior();
  }, [fetchBehavior]);

  // Synchronize automatically when a check-in is logged anywhere in the app
  useEffect(() => {
    const subscription = DeviceEventEmitter.addListener('focusloop:checkin_recorded', () => {
      fetchBehavior();
    });
    return () => {
      subscription.remove();
    };
  }, [fetchBehavior]);

  const refreshEngine = async () => {
    await behaviorService.refresh();
    await fetchBehavior();
  };

  return {
    summary,
    patterns,
    isLoading,
    error,
    refresh: fetchBehavior,
    refreshEngine,
  };
}

