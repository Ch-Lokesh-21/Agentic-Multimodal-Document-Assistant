import { useState } from "react";
import { useAuth } from "../context/useAuth";

interface UseSignupReturn {
  handleSignup: (email: string, password: string) => Promise<boolean>;
  isLoading: boolean;
  error: string | null;
}

export const useSignup = (): UseSignupReturn => {
  const { signup } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignup = async (
    email: string,
    password: string,
  ): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      await signup(email, password);
      return true;
    } catch (err) {
      const message =
        err instanceof Error && "response" in err
          ? (err as any).response?.data?.detail || "Signup failed"
          : "Signup failed";
      setError(message);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return { handleSignup, isLoading, error };
};
