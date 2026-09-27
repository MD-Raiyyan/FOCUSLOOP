import { CheckinStatus } from './checkin';

export type TaskFrequency = 'once' | 'daily';

export interface TaskBase {
  name: string;
  description?: string | null;
  category?: string;
  planned_time?: string; // HH:MM
  target_duration_minutes?: string;
  frequency?: TaskFrequency;
  active?: boolean;
}

export interface TaskCreate extends TaskBase {
  user_id?: string;
}

export interface TaskUpdate {
  name?: string;
  description?: string | null;
  category?: string;
  planned_time?: string;
  target_duration_minutes?: string;
  frequency?: TaskFrequency;
  active?: boolean;
}

export interface TaskResponse extends TaskBase {
  id: string;
  user_id: string;
  today_status?: CheckinStatus | null;
  checkin_id?: string | null;
  created_at: string;
  updated_at: string;
}

