import React from "react";
import { MessageList } from "./MessageList";
import { QueryInput } from "./QueryInput";
import type { SessionMessage } from "../../../../utils/types";

interface QueryPanelProps {
  sessionName: string;
  sessionDescription?: string | null;
  messages: SessionMessage[];
  isLoading: boolean;
  error?: string | undefined | null;
  onSubmitQuery: (query: string) => Promise<void>;
}

export const QueryPanel: React.FC<QueryPanelProps> = ({
  sessionName,
  sessionDescription,
  messages,
  isLoading,
  error,
  onSubmitQuery,
}) => {
  return (
    <div className="flex-1 flex flex-col bg-white">
      <div className="border-b border-gray-200 p-4 bg-blue-50">
        <h2 className="text-lg font-semibold text-gray-900">{sessionName}</h2>
        {sessionDescription && (
          <p className="text-sm text-gray-600">{sessionDescription}</p>
        )}
      </div>

      <div className="flex-1 flex flex-col min-h-0">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>

      {error && (
        <div className="p-4 bg-red-50 border-t border-red-200">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <QueryInput onSubmit={onSubmitQuery} isLoading={isLoading} />
    </div>
  );
};
