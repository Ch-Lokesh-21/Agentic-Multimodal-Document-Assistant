const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  ENDPOINTS: {
    AUTH: {
      SIGNUP: "/auth/signup",
      LOGIN: "/auth/login",
      LOGOUT: "/auth/logout",
      REFRESH: "/auth/refresh",
    },
    SESSIONS: {
      CREATE: "/sessions",
      LIST: "/sessions",
      GET: (id: string) => `/sessions/${id}`,
      DELETE: (id: string) => `/sessions/${id}`,
      MESSAGES: (sessionId: string) => `/sessions/${sessionId}/messages`,
    },
    DOCUMENTS: {
      UPLOAD: (sessionId: string) => `/sessions/${sessionId}/upload`,
      LIST: (sessionId: string) => `/sessions/${sessionId}/documents`,
      GET: (id: string) => `/documents/${id}`,
      DELETE: (id: string) => `/documents/${id}`,
      RETRY: (id: string) => `/documents/${id}/retry`,
    },
    QUERY: {
      ASK: (sessionId: string) => `/sessions/${sessionId}/query`,
      STREAM: (sessionId: string) => `/sessions/${sessionId}/query/stream`,
    },
  },
};
