import { useState } from "react";
import api from "../../../../lib/api";
import { API_CONFIG } from "../../../../app/config/api";
import type { QueryResponse, SessionMessage } from "../types";

interface UseQueryReturn {
  askQuery: (sessionId: string, query: string) => Promise<SessionMessage>;
  isLoading: boolean;
  error: string | null;
}

export const useQuery = (): UseQueryReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const askQuery = async (
    sessionId: string,
    query: string,
  ): Promise<SessionMessage> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<QueryResponse>(
        API_CONFIG.ENDPOINTS.QUERY.ASK(sessionId),
        {
          query,
          stream: false,
          include_sources: true,
        },
      );

      const queryResponse: QueryResponse = response.data;
      return {
        id: `msg_${Date.now()}`,
        session_id: queryResponse.session_id,
        role: "assistant",
        content: queryResponse.answer,
        metadata: {
          citations: queryResponse.citations,
          routing: queryResponse.routing,
          visual_decision: queryResponse.visual_decision,
          processing_time_ms: queryResponse.processing_time_ms,
        },
        created_at: new Date().toISOString(),
      };
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Failed to send query"
          : "Failed to send query";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    askQuery,
    isLoading,
    error,
  };
};
