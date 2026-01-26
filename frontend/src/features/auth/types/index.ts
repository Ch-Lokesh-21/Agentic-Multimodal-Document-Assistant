export interface UserSignupRequest {
  email: string;
  password: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface TokenPayload {
  sub: string;
  email: string;
  exp: number;
  iat: number;
  type: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  token: TokenResponse;
  refresh_token: string | null;
  refresh_token_expires_in: number | null;
  user_id: string;
}

export interface UserResponse {
  id: string;
  email: string;
  is_active: boolean | null;
  is_verified: boolean | null;
  created_at: string | null;
}

export interface CurrentUser {
  id: string;
  email: string;
}

export type User = UserResponse;
