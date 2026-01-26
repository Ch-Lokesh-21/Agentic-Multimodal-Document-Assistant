export interface SessionCreate {
  name: string;
  description: string | null;
}

export interface SessionResponse {
  id: string;
  session_id: string;
  name: string;
  description: string | null;
  document_count: number;
  created_at: string;
  last_activity_at: string;
  is_active: boolean;
}

export type Session = SessionResponse;
