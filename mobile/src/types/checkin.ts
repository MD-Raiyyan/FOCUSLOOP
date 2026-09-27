export type CheckinStatus = 'done' | 'partial' | 'missed';

export interface CheckinBase {
  task_id: string;
  date: string; // YYYY-MM-DD
  status: CheckinStatus;
  completed_at?: string | null;
  actual_start_time?: string | null;
  duration_minutes?: number | null;
  start_delay_minutes?: number | null;
  notes?: string | null;
}

export interface CheckinCreate extends CheckinBase {
  user_id?: string;
}

export interface CheckinResponse extends CheckinBase {
  id: string;
  user_id: string;
  created_at: string;
}
