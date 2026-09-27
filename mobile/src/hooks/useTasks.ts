import { useState, useEffect, useCallback, useRef } from 'react';
import { DeviceEventEmitter } from 'react-native';
import { TaskResponse, TaskCreate } from '../types/tasks';
import { taskService } from '../services/tasks';
import { checkinService } from '../services/checkin';
import { CheckinCreate, CheckinResponse, CheckinStatus } from '../types/checkin';
import { getLocalDateString } from '../utils/formatters';

export function useTasks() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [checkins, setCheckins] = useState<CheckinResponse[]>([]);
  const [checkinsLoading, setCheckinsLoading] = useState<boolean>(true);
  const [checkinsError, setCheckinsError] = useState<string | null>(null);

  const [inFlightTasks, setInFlightTasks] = useState<Record<string, boolean>>({});
  const inFlightRef = useRef<Record<string, boolean>>({});

  const fetchTasks = useCallback(async (date?: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const targetDate = date || getLocalDateString();
      const data = await taskService.getTasks(true, targetDate);
      setTasks(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load tasks');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchCheckins = useCallback(async (date?: string, taskId?: string) => {
    try {
      setCheckinsLoading(true);
      setCheckinsError(null);
      const data = await checkinService.getCheckins(date, taskId);
      setCheckins(data);
    } catch (err: any) {
      setCheckinsError(err.message || "Couldn't load check-in history.");
    } finally {
      setCheckinsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    fetchCheckins();
  }, [fetchTasks, fetchCheckins]);

  const createTask = async (payload: TaskCreate): Promise<TaskResponse> => {
    const newTask = await taskService.createTask(payload);
    setTasks((prev) => [newTask, ...prev]);
    return newTask;
  };

  const deleteTask = async (taskId: string): Promise<void> => {
    await taskService.deleteTask(taskId);
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
  };

  const checkinTask = async (
    taskId: string,
    status: CheckinStatus,
    startDelayMinutes?: number,
    durationMinutes?: number,
    notes?: string
  ): Promise<CheckinResponse | null> => {
    // Prevent duplicate rapid taps while in-flight
    if (inFlightRef.current[taskId]) {
      return null;
    }

    inFlightRef.current[taskId] = true;
    setInFlightTasks((prev) => ({ ...prev, [taskId]: true }));

    // Optimistically reflect status in task list
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, today_status: status } : t))
    );

    try {
      const today = getLocalDateString();
      const payload: CheckinCreate = {
        task_id: taskId,
        date: today,
        status,
        start_delay_minutes: startDelayMinutes,
        duration_minutes: durationMinutes,
        notes,
      };
      const res = await checkinService.createCheckin(payload);

      // Refresh check-ins history
      await fetchCheckins();
      // Sync tasks from backend to obtain authoritative occurrence & history state
      const updatedTasks = await taskService.getTasks(true, today);
      setTasks(updatedTasks);

      // Emit check-in recorded event to refresh behavior summary and profile hooks across the app
      DeviceEventEmitter.emit('focusloop:checkin_recorded', res);

      return res;
    } catch (err) {
      // Re-fetch to roll back any optimistic mismatch on error
      await fetchTasks();
      throw err;
    } finally {
      delete inFlightRef.current[taskId];
      setInFlightTasks((prev) => {
        const next = { ...prev };
        delete next[taskId];
        return next;
      });
    }
  };

  return {
    tasks,
    isLoading,
    error,
    refreshTasks: fetchTasks,
    createTask,
    deleteTask,
    checkinTask,
    inFlightTasks,
    checkins,
    checkinsLoading,
    checkinsError,
    fetchCheckins,
    refreshCheckins: fetchCheckins,
  };
}

