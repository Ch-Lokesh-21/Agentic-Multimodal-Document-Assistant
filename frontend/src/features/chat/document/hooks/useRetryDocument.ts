import api from "../../../../lib/api";
import { API_CONFIG } from "../../../../app/config/api";
import type { Document } from "../types";

export const useRetryDocument = () => {
  const retryDocument = async (documentId: string): Promise<Document> => {
    const response = await api.post(
      API_CONFIG.ENDPOINTS.DOCUMENTS.RETRY(documentId),
    );
    return response.data.document || response.data;
  };
  return { retryDocument };
};
