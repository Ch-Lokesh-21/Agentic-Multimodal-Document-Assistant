import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { LoginPage } from "../../features/auth/components/LoginPage";
import { SignupPage } from "../../features/auth/components/SignupPage";
import { ChatPage } from "../../features/chat/components/ChatPage";
import { ProtectedRoute } from "./ProtectedRoute";

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route
        path="/chat/:sessionId?"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/chat" replace />} />
      <Route
        path="*"
        element={<p className="text-center mt-4">Page not found</p>}
      />
    </Routes>
  );
};
