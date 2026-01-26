import React from "react";
import { DocumentUpload } from "./DocumentUpload";
import type { DocumentResponse } from "../types";

interface DocumentPanelProps {
  documents: DocumentResponse[];
  isLoading: boolean;
  onUpload: (file: File) => Promise<void>;
  onDelete: (documentId: string) => void;
  onRetry?: (documentId: string) => void;
}

export const DocumentPanel: React.FC<DocumentPanelProps> = ({
  documents,
  isLoading,
  onUpload,
  onDelete,
  onRetry,
}) => {
  return (
    <div className="w-64 border-l border-gray-200 flex flex-col bg-white">
      <div className="p-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900 text-sm mb-2">Documents</h3>
        <DocumentUpload onUpload={onUpload} isLoading={isLoading} />
        {isLoading && (
          <div className="mt-2 text-xs text-blue-600">Uploading...</div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {documents.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <p className="text-sm">No documents yet</p>
            <p className="text-xs mt-1">Upload files to get started</p>
          </div>
        ) : (
          <div className="space-y-2 p-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-2 bg-blue-50 rounded-lg group border border-blue-100"
              >
                <p className="text-xs font-medium text-gray-900 truncate">
                  {doc.file_name}
                </p>
                <p className="text-xs text-gray-500">
                  {(doc.file_size / 1024).toFixed(1)} KB
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      doc.status === "indexed"
                        ? "bg-green-100 text-green-700"
                        : doc.status === "processing"
                        ? "bg-yellow-100 text-yellow-700"
                        : doc.status === "failed"
                        ? "bg-red-100 text-red-700"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {doc.status}
                  </span>
                  {doc.status === "failed" && onRetry && (
                    <button
                      onClick={() => onRetry(doc.id)}
                      className="ml-2 text-xs text-orange-600 hover:bg-orange-100 px-2 py-0.5 rounded border border-orange-200"
                    >
                      Retry
                    </button>
                  )}
                  <button
                    onClick={() => onDelete(doc.id)}
                    className="hidden group-hover:inline ml-auto text-xs text-red-600 hover:bg-red-100 px-2 py-0.5 rounded"
                  >
                    Delete
                  </button>
                </div>
                {doc.status === "failed" && doc.error_message && (
                  <div className="text-xs text-red-500 mt-1">{doc.error_message}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
