import { useState, useEffect, useCallback } from 'react';
import {
  ExperimentResponse,
  ExperimentResultResponse,
} from '../types/experiments';
import { experimentService } from '../services/experiments';

export function useExperiments() {
  const [experiments, setExperiments] = useState<ExperimentResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExperiments = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await experimentService.getExperiments();
      setExperiments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load experiments');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExperiments();
  }, [fetchExperiments]);

  const suggestExperiment = async (): Promise<ExperimentResponse[]> => {
    const data = await experimentService.suggestExperiment();
    setExperiments(data);
    return data;
  };

  const startExperiment = async (id: string): Promise<ExperimentResponse> => {
    const updated = await experimentService.updateExperiment(id, { status: 'active' });
    await fetchExperiments();
    return updated;
  };

  const evaluateExperiment = async (
    id: string
  ): Promise<ExperimentResultResponse> => {
    const result = await experimentService.evaluateExperiment(id);
    await fetchExperiments();
    return result;
  };

  return {
    experiments,
    isLoading,
    error,
    refreshExperiments: fetchExperiments,
    suggestExperiment,
    startExperiment,
    evaluateExperiment,
  };
}
