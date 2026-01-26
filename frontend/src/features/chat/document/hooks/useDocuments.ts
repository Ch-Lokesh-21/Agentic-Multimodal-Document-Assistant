import { useState } from "react";
import type { Document } from "../types";
import api from "../../../../lib/api";
import { API_CONFIG } from "../../../../app/config/api";

interface UseDocumentsReturn {
  documents: Document[];
  isLoading: boolean;
  error: string | null;
  fetchDocuments: (sessionId: string) => Promise<void>;
  deleteDocument: (documentId: string) => Promise<void>;
}

export const useDocuments = (): UseDocumentsReturn => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = async (sessionId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get(`/sessions/${sessionId}/documents`);
      setDocuments(response.data.documents || []);
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Failed to fetch documents"
          : "Failed to fetch documents";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteDocument = async (documentId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await api.delete(API_CONFIG.ENDPOINTS.DOCUMENTS.DELETE(documentId));
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
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
    documents,
    isLoading,
    error,
    fetchDocuments,
    deleteDocument,
  };
};
