import { useState } from "react";
import { useAuth } from "../context/useAuth";

interface UseLoginReturn {
  handleLogin: (email: string, password: string) => Promise<boolean>;
  isLoading: boolean;
  error: string | null;
}

export const useLogin = (): UseLoginReturn => {
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (
    email: string,
    password: string,
  ): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      await login(email, password);
      return true;
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Login failed"
          : "Login failed";
      setError(message);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return { handleLogin, isLoading, error };
};
