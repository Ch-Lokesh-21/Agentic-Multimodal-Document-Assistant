import React, { useState } from "react";
import type { SessionResponse } from "../types";
import { LogoutButton } from "../../../../app/components/ui/LogoutButton";

interface SessionPanelProps {
  sessions: SessionResponse[];
  currentSessionId?: string;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onCreateSession: (name: string, description?: string) => void;
}

export const SessionPanel: React.FC<SessionPanelProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onDeleteSession,
  onCreateSession,
}) => {
  const [showModal, setShowModal] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState("");
  const [newSessionDescription, setNewSessionDescription] = useState("");

  const handleCreateSession = () => {
    if (!newSessionTitle.trim()) {
      alert("Please enter a session title");
      return;
    }
    onCreateSession(newSessionTitle, newSessionDescription);
    setNewSessionTitle("");
    setNewSessionDescription("");
    setShowModal(false);
  };

  const handleDelete = (sessionId: string) => {
    if (window.confirm("Are you sure you want to delete this session?")) {
      onDeleteSession(sessionId);
    }
  };

  return (
    <>
      <div className="w-64 border-r border-gray-200 flex flex-col bg-white">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={() => setShowModal(true)}
            className="w-full cursor-pointer px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            + New Session
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {sessions.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <p className="text-sm">No sessions yet</p>
              <p className="text-xs mt-1">Create one to get started</p>
            </div>
          ) : (
            <div className="space-y-1 p-2">
              {sessions.map((session) => (
                <div key={session.id} className="group relative">
                  <button
                    onClick={() => onSelectSession(session.session_id)}
                    className={`w-full cursor-pointer text-left px-3 py-2 rounded-lg transition ${
                      currentSessionId === session.session_id
                        ? "bg-blue-50 text-blue-900 border border-blue-200"
                        : "text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    <p className="text-sm font-medium truncate">
                      {session.name}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {session.document_count} document
                      {session.document_count !== 1 ? "s" : ""}
                    </p>
                  </button>
                  <button
                    onClick={() => handleDelete(session.session_id)}
                    className="hidden hover:underline cursor-pointer group-hover:block absolute right-2 top-2 px-2 py-1 text-xs text-red-600 hover:bg-red-100 rounded"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      <LogoutButton/>
      </div>


      {showModal && (
        <div className="fixed inset-0 bg-transparent flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 shadow-xl">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Create New Session
            </h2>
            <input
              type="text"
              value={newSessionTitle}
              onChange={(e) => setNewSessionTitle(e.target.value)}
              placeholder="Session title"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <textarea
              value={newSessionDescription}
              onChange={(e) => setNewSessionDescription(e.target.value)}
              placeholder="Session description (optional)"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
            <div className="flex gap-2">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateSession}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
