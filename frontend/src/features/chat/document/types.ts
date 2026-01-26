export type DocumentStatus = "uploaded" | "processing" | "indexed" | "failed";

export interface DocumentCreate {
  user_id: string;
  session_id: string;
  file_path: string;
  file_size: number;
  content_type: string;
  file_name: string;
}

export interface DocumentResponse {
  id: string;
  session_id: string;
  file_name: string;
  file_size: number;
  content_type: string;
  status: DocumentStatus;
  chunk_count: number | null;
  page_count: number | null;
  error_message: string | null;
  processed_at: string | null;
  created_at: string;
}

export type Document = DocumentResponse;
