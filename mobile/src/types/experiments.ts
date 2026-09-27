export interface ExperimentBase {
  title: string;
  description: string;
  hypothesis: string;
  intervention_type?: string;
  start_date: string; // YYYY-MM-DD
  end_date?: string | null;
  target_metric: string;
  baseline_value?: number | null;
  target_value?: number | null;
  pattern_id?: string | null;
}

export interface ExperimentCreate extends ExperimentBase {
  user_id?: string;
}

export interface ExperimentUpdate {
  status?: string; // active, completed, dismissed
  end_date?: string | null;
}

export interface ExperimentResultResponse {
  id: string;
  experiment_id: string;
  metric_name: string;
  before_value?: number | null;
  after_value?: number | null;
  change_value?: number | null;
  percent_change?: number | null;
  conclusion: string;
  result_summary: string;
  created_at: string;
}

export interface ExperimentResponse extends ExperimentBase {
  id: string;
  user_id: string;
  status: string; // active, completed, dismissed
  created_at: string;
  results: ExperimentResultResponse[];
}

export interface ExperimentEvaluationRequest {
  experiment_id: string;
}
