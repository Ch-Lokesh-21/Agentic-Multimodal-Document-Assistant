import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../../features/auth/context/useAuth";
import { Toast } from "./Toast";

export const LogoutButton: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [toast, setToast] = React.useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const handleLogout = async () => {
    try {
      await logout();
      setToast({ message: "Logged out successfully", type: "success" });
      setTimeout(() => {
        navigate("/login");
      }, 1200);
    } catch (error) {
    
      setToast({ message: "Logout failed", type: "error" });
    }
  };

  return (
    <div className="p-2 w-full flex justify-center border-t border-gray-200 bg-white">
      <button
        className="px-4 py-2 rounded bg-red-500 hover:bg-red-600 cursor-pointer w-full text-white font-medium"
        onClick={handleLogout}
      >
        Logout
      </button>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};
