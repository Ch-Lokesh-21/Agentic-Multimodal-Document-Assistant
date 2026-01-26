import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useSignup } from "../hooks/useSignup";
import { Input } from "../../../app/components/ui/Input";
import { Button } from "../../../app/components/ui/Button";
import { Card } from "../../../app/components/ui/Card";

export const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  const { handleSignup, isLoading, error } = useSignup();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});

  const validateForm = (): Record<string, string> => {
    const errors: Record<string, string> = {};

    if (!email) {
      errors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Invalid email format";
    }

    if (!password) {
      errors.password = "Password is required";
    } else if (password.length < 8) {
      errors.password = "Password must be at least 8 characters";
    } else if (!/[A-Z]/.test(password)) {
      errors.password = "Password must contain uppercase letter";
    } else if (!/[a-z]/.test(password)) {
      errors.password = "Password must contain lowercase letter";
    } else if (!/[0-9]/.test(password)) {
      errors.password = "Password must contain a digit";
    }

    if (!confirmPassword) {
      errors.confirmPassword = "Please confirm your password";
    } else if (password !== confirmPassword) {
      errors.confirmPassword = "Passwords do not match";
    }

    return errors;
  };

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    e.preventDefault();
    setValidationErrors({});

    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    const success = await handleSignup(email, password);
    if (success) {
      navigate("/chat");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Create Account
          </h1>
          <p className="text-gray-600 dark:text-gray-400">Join us today</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setEmail(e.target.value)
            }
            error={validationErrors.email}
            disabled={isLoading}
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setPassword(e.target.value)
            }
            error={validationErrors.password}
            disabled={isLoading}
          />

          <Input
            label="Confirm Password"
            type="password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setConfirmPassword(e.target.value)
            }
            error={validationErrors.confirmPassword}
            disabled={isLoading}
          />

          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
            className="w-full"
          >
            Create Account
          </Button>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-blue-600 dark:text-blue-400 font-medium hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
};
