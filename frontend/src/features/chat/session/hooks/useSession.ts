import { useState } from "react";
import type { Session } from "../types";
import api from "../../../../lib/api";
import { API_CONFIG } from "../../../../app/config/api";
import type { SessionMessage } from "../../query/types";

interface UseSessionReturn {
  sessions: Session[];
  currentSession: Session | null;
  messages: SessionMessage[];
  isLoading: boolean;
  error: string | null;
  fetchSessions: () => Promise<void>;
  createSession: (
    title: string,
    description?: string | null,
  ) => Promise<Session>;
  loadSession: (
    sessionId: string,
  ) => Promise<{ session: Session; messages: SessionMessage[] }>;
  deleteSession: (sessionId: string) => Promise<void>;
  addMessage: (message: any) => void;
}

export const useSession = (): UseSessionReturn => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<SessionMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get(API_CONFIG.ENDPOINTS.SESSIONS.LIST);
      setSessions(response.data.sessions || []);
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Failed to fetch sessions"
          : "Failed to fetch sessions";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const createSession = async (
    title: string,
    description?: string | null,
  ): Promise<Session> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post(API_CONFIG.ENDPOINTS.SESSIONS.CREATE, {
        name: title,
        description: description || null,
      });

      const newSession = response.data;
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSession(newSession);
      setMessages([]);

      return newSession;
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Failed to create session"
          : "Failed to create session";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const loadSession = async (
    sessionId: string,
  ): Promise<{ session: Session; messages: SessionMessage[] }> => {
    setIsLoading(true);
    setError(null);

    try {
      const [sessionResponse, messagesResponse] = await Promise.all([
        api.get(API_CONFIG.ENDPOINTS.SESSIONS.GET(sessionId)),
        api.get(API_CONFIG.ENDPOINTS.SESSIONS.MESSAGES(sessionId)),
      ]);

      const sessionData = sessionResponse.data;
      const messagesData = messagesResponse.data.messages || [];

      setCurrentSession(sessionData);
      setMessages(messagesData);

      return { session: sessionData, messages: messagesData };
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Failed to load session"
          : "Failed to load session";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sessionId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await api.delete(API_CONFIG.ENDPOINTS.SESSIONS.DELETE(sessionId));
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));

      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Failed to delete session"
          : "Failed to delete session";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const addMessage = (message: SessionMessage): void => {
    setMessages((prev) => [...prev, message]);
  };

  return {
    sessions,
    currentSession,
    messages,
    isLoading,
    error,
    fetchSessions,
    createSession,
    loadSession,
    deleteSession,
    addMessage,
  };
};
