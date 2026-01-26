import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CurrentUser, AuthResponse } from "../types";
import { AuthContext } from "./auth";
import api from "../../../lib/api";
import { setAccessToken, clearAccessToken } from "./authService";
import { API_CONFIG } from "../../../app/config/api";


export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [, setToken] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const init = async (): Promise<void> => {
      try {
        const resp = await api.post(API_CONFIG.ENDPOINTS.AUTH.REFRESH);
        const data: AuthResponse = resp.data;
        const token = data.token?.access_token ?? null;
        if (token) {
          setToken(token);
          setAccessToken(token);
        }

        if (data.user_id) {
          setUser({ id: data.user_id, email: (data as any).user_email ?? "" });
        }
      } catch (e: any) {
        if (e?.response?.status === 401) {
          setUser(null);
          setToken(null);
          clearAccessToken();
          navigate("/login");
        }
      } finally {
        setIsLoading(false);
      }
    };

    init();
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    const response = await api.post(API_CONFIG.ENDPOINTS.AUTH.LOGIN, {
      email,
      password,
    });

    const data: AuthResponse = response.data;
    const token = data.token?.access_token ?? null;

    setUser({ id: data.user_id, email });
    setToken(token);
    setAccessToken(token);
  };

  const signup = async (email: string, password: string): Promise<void> => {
    const response = await api.post(API_CONFIG.ENDPOINTS.AUTH.SIGNUP, {
      email,
      password,
    });

    const data: AuthResponse = response.data;
    const token = data.token?.access_token ?? null;

    setUser({ id: data.user_id, email });
    setToken(token);
    setAccessToken(token);
  };

  const logout = async (): Promise<void> => {
    try {
      await api.post(API_CONFIG.ENDPOINTS.AUTH.LOGOUT);
    } finally {
      clearAccessToken();
      setToken(null);
      setUser(null);
      navigate("/login");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;
