import React, { useEffect, useRef } from "react";
import type { SessionMessage } from "../../../../utils/types";
import type { Citation } from "../types";

interface MessageListProps {
  messages: SessionMessage[];
  isLoading: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
}) => {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-gray-50 space-y-4 min-h-0">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-center">
          <div className="text-gray-500">
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm">
              Start by uploading a document and asking a question
            </p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => {
            const citations = message.metadata?.citations as
              | Citation[]
              | undefined;
            const hasCitations = citations && citations.length > 0;

            return (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-2xl ${
                    message.role === "user"
                      ? "bg-blue-600 text-white px-4 py-2 rounded-lg"
                      : "bg-white border border-gray-200 text-gray-900 rounded-lg"
                  }`}
                >
                  <div className={message.role === "assistant" ? "p-4" : ""}>
                    <p className="text-sm whitespace-pre-wrap">
                      {message.content}
                    </p>
                    <p className="text-xs mt-1 opacity-75">
                      {new Date(message.created_at).toLocaleTimeString()}
                    </p>
                  </div>

                  {/* Citations Section */}
                  {message.role === "assistant" && hasCitations && (
                    <div className="border-t border-gray-200 p-3 bg-blue-50">
                      <h4 className="text-xs font-semibold text-gray-700 mb-2">
                        Sources ({citations.length})
                      </h4>
                      <div className="space-y-2">
                        {citations.map((citation, idx) => (
                          <div
                            key={idx}
                            className="text-xs bg-white border border-blue-200 rounded p-2"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium text-gray-900">
                                    {citation.source_id}
                                  </span>
                                  {citation.page_number && (
                                    <span className="text-gray-500">
                                      Page {citation.page_number}
                                    </span>
                                  )}
                                  <span
                                    className={`px-2 py-0.5 rounded text-xs ${
                                      citation.source_type === "document"
                                        ? "bg-green-100 text-green-700"
                                        : citation.source_type === "web"
                                          ? "bg-blue-100 text-blue-700"
                                          : "bg-purple-100 text-purple-700"
                                    }`}
                                  >
                                    {citation.source_type}
                                  </span>
                                </div>
                                {citation.snippet && (
                                  <p className="text-gray-600 italic line-clamp-2">
                                    "{citation.snippet}"
                                  </p>
                                )}
                                {citation.url && (
                                  <a
                                    href={citation.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline mt-1 inline-block"
                                  >
                                    {citation.url}
                                  </a>
                                )}
                              </div>
                              <div className="flex items-center gap-1">
                                <div className="flex flex-col items-end">
                                  <span className="text-gray-400 text-xs">
                                    {Math.round(citation.confidence * 100)}%
                                  </span>
                                  <div className="w-12 h-1 bg-gray-200 rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-blue-600"
                                      style={{
                                        width: `${citation.confidence * 100}%`,
                                      }}
                                    />
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 px-4 py-2 rounded-lg">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                    style={{ animationDelay: "0.4s" }}
                  ></div>
                </div>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </>
      )}
    </div>
  );
};
