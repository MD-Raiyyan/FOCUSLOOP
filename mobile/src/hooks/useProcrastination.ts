import { useState, useEffect, useCallback } from 'react';
import {
  ProcrastinationEventResponse,
  ProcrastinationEventCreate,
  ProcrastinationEventEnd,
} from '../types/procrastination';
import { procrastinationService } from '../services/procrastination';

export function useProcrastination() {
  const [events, setEvents] = useState<ProcrastinationEventResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await procrastinationService.getEvents();
      setEvents(data);
    } catch (err: any) {
      setError(err.message || "Couldn't load delay history.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const startEvent = async (
    payload?: ProcrastinationEventCreate
  ): Promise<ProcrastinationEventResponse> => {
    return procrastinationService.startEvent(payload);
  };

  const endEvent = async (
    eventId: string,
    payload?: ProcrastinationEventEnd
  ): Promise<ProcrastinationEventResponse> => {
    const res = await procrastinationService.endEvent(eventId, payload);
    // Refresh history so the newly ended episode appears in the historical list
    await fetchEvents();
    return res;
  };

  return {
    events,
    isLoading,
    error,
    fetchEvents,
    refreshEvents: fetchEvents,
    startEvent,
    endEvent,
  };
}
