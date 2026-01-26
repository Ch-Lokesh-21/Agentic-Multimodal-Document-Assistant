import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useSession } from "../session/hooks/useSession";
import { useQuery } from "../query/hooks/useQuery";
import { useDocument } from "../document/hooks/useDocument";
import { useDocuments } from "../document/hooks/useDocuments";
import { SessionPanel } from "../session/components/SessionPanel";
import { DocumentPanel } from "../document/components/DocumentPanel";
import { QueryPanel } from "../query/components/QueryPanel";
import { WelcomeScreen } from "./WelcomeScreen";
import { Toast } from "../../../app/components/ui/Toast";
import { useRetryDocument } from "../document/hooks/useRetryDocument";

export const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const { retryDocument } = useRetryDocument();
  const handleRetryDocument = async (documentId: string): Promise<void> => {
    if (!currentSession) return;
    try {
      await retryDocument(documentId);
      setToast({ message: "Retry started for document", type: "info" });
      await fetchDocuments(currentSession.session_id);
    } catch (error) {
      setToast({ message: "Failed to retry document", type: "error" });
    }
  };
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const {
    sessions,
    currentSession,
    messages,
    error: sessionError,
    fetchSessions,
    createSession,
    loadSession,
    deleteSession,
    addMessage,
  } = useSession();

  const { askQuery, isLoading: queryLoading, error: queryError } = useQuery();
  const { uploadDocument, isLoading: documentLoading } = useDocument();
  const {
    documents,
    error: documentsError,
    fetchDocuments,
    deleteDocument,
  } = useDocuments();

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (sessionId && sessionId !== currentSession?.session_id) {
      loadSession(sessionId);
      fetchDocuments(sessionId);
    }
  }, [sessionId]);

  const handleCreateSession = async (
    name: string,
    description?: string | null,
  ): Promise<void> => {
    try {
      const newSession = await createSession(name, description || null);
      navigate(`/chat/${newSession.session_id}`);
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const handleSelectSession = (sessionId: string): void => {
    navigate(`/chat/${sessionId}`);
  };

  const handleDeleteSession = async (sessionId: string): Promise<void> => {
    try {
      await deleteSession(sessionId);
      await fetchSessions(); // Reload the sessions list
      setToast({ message: "Session deleted successfully", type: "success" });
      if (currentSession?.session_id === sessionId) {
        navigate("/chat");
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
      setToast({ message: "Failed to delete session", type: "error" });
    }
  };

  const handleAskQuery = async (query: string): Promise<void> => {
    if (!currentSession) return;

    try {
      const userMessage = {
        id: Date.now().toString(),
        session_id: currentSession.session_id,
        role: "user" as const,
        content: query,
        created_at: new Date().toISOString(),
        metadata: null,
      };
      addMessage(userMessage as any);

      const assistantMessage = await askQuery(currentSession.session_id, query);
      addMessage(assistantMessage);
    } catch (error) {
      console.error("Failed to ask query:", error);
    }
  };

  const handleUploadDocument = async (file: File): Promise<void> => {
    if (!currentSession) return;

    try {
      await uploadDocument(file, currentSession.session_id);
      await fetchDocuments(currentSession.session_id);
    } catch (error) {
      console.error("Failed to upload document:", error);
    }
  };

  const handleDeleteDocument = (documentId: string): void => {
    deleteDocument(documentId);
  };

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      <SessionPanel
        sessions={sessions}
        currentSessionId={currentSession?.session_id}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onCreateSession={handleCreateSession}
      />

      {currentSession ? (
        <QueryPanel
          sessionName={currentSession.name}
          sessionDescription={currentSession.description}
          messages={messages}
          isLoading={queryLoading}
          error={sessionError || queryError || documentsError}
          onSubmitQuery={handleAskQuery}
        />
      ) : (
        <WelcomeScreen onCreateSession={() => {}} />
      )}

      {currentSession && (
        <DocumentPanel
          documents={documents}
          isLoading={documentLoading}
          onUpload={handleUploadDocument}
          onDelete={handleDeleteDocument}
          onRetry={handleRetryDocument}
        />
      )}
    </div>
  );
};
