export interface UserIdentity {
  id: string;
  name: string;
  username?: string | null;
  email?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  timezone?: string | null;
}

export interface ProfileVisibilitySettings {
  current_level: boolean;
  behavior_score: boolean;
  improvement_score: boolean;
  experiment_effectiveness: boolean;
  consistency: boolean;
  behavioral_patterns: boolean;
}

export interface ProfileVisibilityUpdate {
  current_level?: boolean;
  behavior_score?: boolean;
  improvement_score?: boolean;
  experiment_effectiveness?: boolean;
  consistency?: boolean;
  behavioral_patterns?: boolean;
}

export interface ProgressCurvePoint {
  date: string;
  progress_score: number;
  trend: 'initial' | 'improving' | 'stable' | 'setback' | 'recovery';
  metric_context?: string | null;
}

export interface PersonalMetrics {
  current_level: string;
  level_info: Record<string, any>;
  /** Scale: 0.0 to 100.0 score */
  behavior_score: number;
  /** Scale: 0.0 to 100.0 score */
  improvement_score: number;
  /** Scale: 0.0 to 100.0 score / percentage */
  experiment_effectiveness: number;
  /** Scale: 0.0 to 100.0 score / percentage */
  consistency: number;
}

export interface PersonalProfileResponse {
  identity: UserIdentity;
  visibility_settings: ProfileVisibilitySettings;
  metrics: PersonalMetrics;
  progress_curve: ProgressCurvePoint[];
  behavioral_intelligence: Record<string, any>;
  milestones: string[];
  updated_at: string;
}

export interface SocialMetrics {
  /** Scale: 0.0 to 100.0 score */
  improvement_score?: number | null;
  /** Scale: 0.0 to 100.0 score / percentage */
  experiment_effectiveness?: number | null;
  /** Scale: 0.0 to 100.0 score / percentage */
  consistency?: number | null;
  current_level?: string | null;
  /** Scale: 0.0 to 100.0 score */
  behavior_score?: number | null;
}

export interface SocialProfileResponse {
  identity: UserIdentity;
  is_friend: boolean;
  metrics: SocialMetrics;
  progress_curve: ProgressCurvePoint[];
  milestones: string[];
  behavioral_patterns?: Record<string, any>[] | null;
}
