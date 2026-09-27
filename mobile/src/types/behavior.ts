export interface MetricResponse {
  id: string;
  user_id: string;
  metric_type: string;
  metric_value: number;
  time_window_start?: string | null;
  time_window_end?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
}

export interface ContextComparisonPoint {
  context: string;
  label: string;
  value: number;
  sample_size: number;
  unit: string;
}

export interface TimeSeriesPoint {
  date: string;
  value: number;
  sample_size: number;
  unit: string;
}

export interface WindowMetric {
  label: string;
  value: number | null;
  sample_size: number;
  unit: string;
  weighted_value?: number | null;
}

export interface SupportingMetrics {
  pattern_id?: string;
  pattern_type?: string;
  status?: string;
  confidence?: string;
  sample_size?: number;
  distinct_days?: number;
  first_observed_date?: string;
  last_observed_date?: string;
  trend?: string;
  metric_name?: string;
  unit?: string;
  contradiction_detected?: boolean;
  insufficient_evidence?: boolean;
  explanation?: string;
  context_comparison?: ContextComparisonPoint[];
  time_series?: TimeSeriesPoint[];
  historical_window?: WindowMetric;
  recent_window?: WindowMetric;
  [key: string]: any;
}

export interface PatternResponse {
  id: string;
  user_id: string;
  pattern_type: string;
  title: string;
  description: string;
  confidence: string;
  sample_size: number;
  first_detected: string;
  last_detected: string;
  status: string;
  supporting_metrics?: SupportingMetrics | null;
  created_at: string;
}

export interface BehaviorProfileResponse {
  user_id: string;
  profile_data: Record<string, any>;
  model_version: string;
  updated_at: string;
}

export interface BehaviorSummary {
  /** True ratio (0.0 to 1.0) */
  completion_rate: number;
  total_tasks_tracked: number;
  completed_tasks: number;
  missed_tasks: number;
  partial_tasks: number;
  /** Average start delay in minutes. null = no observations, 0 = measured 0 delay */
  average_start_delay_minutes?: number | null;
  best_focus_window: string;
  worst_focus_window: string;
  procrastination_count: number;
  total_procrastination_minutes: number;
  top_distraction_apps: Record<string, any>[];
  active_patterns: PatternResponse[];
  profile?: Record<string, any> | null;
  /** Context date if summary is scoped to a specific day YYYY-MM-DD */
  date?: string | null;
}
