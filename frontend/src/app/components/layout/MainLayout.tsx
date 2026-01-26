import React, { useState } from "react";
import { useAuth } from "../../../features/auth/context/useAuth";

interface MainLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  sidebar,
}) => {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = async (): Promise<void> => {
    await logout();
    window.location.href = "/login";
  };

  return (
    <div className="h-screen flex bg-white">
      {sidebar && (
        <div
          className={`${
            sidebarOpen ? "w-64" : "w-0"
          } transition-all duration-300 overflow-hidden flex flex-col`}
        >
          {sidebar}
        </div>
      )}

      <div className="flex-1 flex flex-col">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg
                className="w-5 h-5 text-gray-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <h1 className="text-xl font-bold text-gray-900">
              Research Paper Assistance
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
};
