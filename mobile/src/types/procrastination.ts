export interface ProcrastinationEventBase {
  task_id?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  duration_seconds?: number | null;
  user_confirmed?: boolean;
  trigger_reason?: string | null;
  context_data?: Record<string, any> | null;
  notes?: string | null;
}

export interface ProcrastinationEventCreate extends ProcrastinationEventBase {
  user_id?: string;
}

export interface ProcrastinationEventEnd {
  ended_at?: string | null;
  trigger_reason?: string | null;
  notes?: string | null;
  context_data?: Record<string, any> | null;
}

export interface ProcrastinationEventResponse extends ProcrastinationEventBase {
  id: string;
  user_id: string;
  created_at: string;
}
