import { useState } from "react";
import type { Document } from "../types";
import api from "../../../../lib/api";
import { API_CONFIG } from "../../../../app/config/api";

interface UseDocumentReturn {
  uploadDocument: (file: File, sessionId: string) => Promise<Document>;
  deleteDocument: (documentId: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const useDocument = (): UseDocumentReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadDocument = async (
    file: File,
    sessionId: string,
  ): Promise<Document> => {
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("session_id", sessionId);

      const response = await api.post(
        API_CONFIG.ENDPOINTS.DOCUMENTS.UPLOAD(sessionId),
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );

      return response.data.data;
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Failed to upload document"
          : "Failed to upload document";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const deleteDocument = async (documentId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await api.delete(API_CONFIG.ENDPOINTS.DOCUMENTS.DELETE(documentId));
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Failed to delete document"
          : "Failed to delete document";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    uploadDocument,
    deleteDocument,
    isLoading,
    error,
  };
};
