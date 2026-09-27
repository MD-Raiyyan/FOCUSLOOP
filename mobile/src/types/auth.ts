export interface UserRegister {
  email: string;
  password: string;
  name?: string;
  username?: string;
  timezone?: string;
}

export interface UserLogin {
  email: string; // email or username
  password: string;
}

export interface AuthUser {
  id: string;
  name: string;
  username?: string | null;
  email?: string | null;
  timezone?: string | null;
  is_active: boolean;
  onboarding_completed?: boolean;
  onboarding_completed_at?: string | null;
  onboarding_step?: string | null;
  age_range?: string | null;
  gender?: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LogoutResponse {
  message: string;
}
