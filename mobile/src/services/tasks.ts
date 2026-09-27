import { api } from './api';
import { TaskCreate, TaskResponse, TaskUpdate } from '../types/tasks';

export const taskService = {
  async getTasks(activeOnly = true, date?: string): Promise<TaskResponse[]> {
    const params = new URLSearchParams();
    params.append('active_only', String(activeOnly));
    if (date) params.append('date', date);
    return api.get<TaskResponse[]>(`/api/v1/tasks?${params.toString()}`);
  },

  async createTask(payload: TaskCreate): Promise<TaskResponse> {
    return api.post<TaskResponse>('/api/v1/tasks', payload);
  },

  async getTask(taskId: string): Promise<TaskResponse> {
    return api.get<TaskResponse>(`/api/v1/tasks/${taskId}`);
  },

  async updateTask(taskId: string, payload: TaskUpdate): Promise<TaskResponse> {
    return api.put<TaskResponse>(`/api/v1/tasks/${taskId}`, payload);
  },

  async deleteTask(taskId: string): Promise<void> {
    return api.delete<void>(`/api/v1/tasks/${taskId}`);
  },
};
