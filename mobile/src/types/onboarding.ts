export interface UserGoal {
  id?: string;
  category: string;
  description: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface UserRoutineContext {
  preferred_time_window?: string | null;
  daily_available_duration?: string | null;
  updated_at?: string;
}

export interface UserChallenge {
  id?: string;
  challenge_text: string;
  source?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface UserInterest {
  id?: string;
  interest_text: string;
  source?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface OnboardingStatus {
  onboarding_completed: boolean;
  onboarding_completed_at?: string | null;
  onboarding_step: string;
  current_step?: string;
  has_partial_data: boolean;
}

export interface OnboardingData {
  onboarding_completed: boolean;
  onboarding_completed_at?: string | null;
  onboarding_step: string;
  name?: string | null;
  age_range?: string | null;
  gender?: string | null;
  goal?: UserGoal | null;
  routine?: UserRoutineContext | null;
  challenges: UserChallenge[];
  interests: UserInterest[];
}

export interface OnboardingUpdatePayload {
  onboarding_step?: string;
  step?: string;
  name?: string;
  age_range?: string;
  gender?: string;
  goal_category?: string;
  goal_description?: string;
  goal?: {
    category: string;
    description?: string;
  };
  preferred_time_window?: string;
  daily_available_duration?: string;
  routine?: {
    preferred_time_window?: string;
    daily_available_duration?: string;
  };
  challenges?: string[];
  interests?: string[];
}

export interface OnboardingCompleteResponse {
  message: string;
  onboarding_completed: boolean;
  onboarding_completed_at: string;
}
