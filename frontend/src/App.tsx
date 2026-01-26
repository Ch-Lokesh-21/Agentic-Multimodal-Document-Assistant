import React from "react";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./features/auth/context/AuthContext";
import { AppRoutes } from "./app/routes";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
