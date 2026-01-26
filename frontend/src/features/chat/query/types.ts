export type MessageRole = "user" | "assistant";

export interface SessionMessageCreate {
  role: MessageRole;
  content: string;
}

export interface SessionMessageResponse {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export type SessionMessage = SessionMessageResponse;

export interface QueryRequest {
  query: string;
  stream: boolean;
  include_sources: boolean;
}

export interface Citation {
  source_type: "document" | "web" | "llm_knowledge";
  source_id: string;
  page_number: number | null;
  url: string | null;
  snippet: string;
  confidence: number;
}

export interface RoutingDecision {
  route: "llm" | "web_search" | "multimodal_rag";
  reasoning: string;
  confidence: number;
  fallback_route: "llm" | "web_search" | "multimodal_rag" | null;
}

export interface VisualDecision {
  requires_visual: boolean;
  reasoning: string;
  visual_type: "full_page" | "diagram" | "table" | "figure" | null;
  confidence: number;
}

export interface SourcePageSelection {
  source_file: string;
  pages: number[];
}

export interface PageSelectionDecision {
  selected_pages: SourcePageSelection[];
  reasoning: string;
}

export interface QueryAnalysisResult {
  classification: "simple" | "complex";
  reasoning: string;
  sub_queries: string[];
  is_comparison: boolean;
  confidence: number;
}

export interface SubQueryResult {
  sub_query: string;
  answer: string;
  citations: Citation[];
}

export interface QueryResponse {
  success: boolean;
  query: string;
  answer: string;
  citations: Citation[];
  routing: RoutingDecision | null;
  visual_decision: VisualDecision | null;
  processing_time_ms: number;
  session_id: string;
}
