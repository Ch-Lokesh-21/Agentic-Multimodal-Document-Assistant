import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  CircularProgress,
  InputAdornment,
  IconButton,
} from "@mui/material";
import { Visibility, VisibilityOff, Home as HomeIcon } from "@mui/icons-material";
import { useSignup } from "../hooks/index.ts";
import type { SignupFormData } from "../types/index.ts"
import { handleSuccess } from "../../../utils/errorHandler.ts";

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const { mutate: signup, isPending } = useSignup();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<SignupFormData>({
    mode: "onBlur",
  });

  const onSubmit = (data: SignupFormData) => {
    const signupData = {
      email: data.email,
      password: data.password,
    };
    signup(signupData, {
      onSuccess: () => {
        handleSuccess("Account created successfully!");
        navigate("/chat");
      },
    });
  };

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword((prev) => !prev);
  };

  return (
    <Box
      className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100"
      sx={{ padding: 2 }}
    >
      <Paper
        elevation={3}
        sx={{
          padding: 4,
          maxWidth: 450,
          width: "100%",
          borderRadius: 2,
          position: "relative",
        }}
      >
        <IconButton
          onClick={() => navigate("/")}
          sx={{
            position: "absolute",
            top: 16,
            left: 16,
            color: "primary.main",
            "&:hover": {
              bgcolor: "primary.light",
              color: "white",
            },
          }}
          aria-label="Go to home"
        >
          <HomeIcon />
        </IconButton>
        <Typography
          variant="h4"
          component="h1"
          gutterBottom
          className="text-center font-bold text-gray-800"
        >
          Create Account
        </Typography>
        <Typography variant="body2" className="text-center text-gray-600 mb-6">
          Sign up to get started
        </Typography>

        <form onSubmit={handleSubmit(onSubmit)}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            margin="normal"
            autoComplete="email"
            autoFocus
            error={!!errors.email}
            helperText={errors.email?.message}
            {...register("email", {
              required: "Email is required",
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: "Invalid email address",
              },
            })}
          />

          <TextField
            fullWidth
            label="Password"
            type={showPassword ? "text" : "password"}
            margin="normal"
            autoComplete="new-password"
            error={!!errors.password}
            helperText={
              errors.password?.message ||
              "Min 8 characters, 1 uppercase, 1 lowercase, 1 digit"
            }
            {...register("password", {
              required: "Password is required",
              minLength: {
                value: 8,
                message: "Password must be at least 8 characters",
              },
              pattern: {
                value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/,
                message:
                  "Password must contain uppercase, lowercase, and digit",
              },
            })}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="toggle password visibility"
                    onClick={togglePasswordVisibility}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Confirm Password"
            type={showConfirmPassword ? "text" : "password"}
            margin="normal"
            autoComplete="new-password"
            error={!!errors.confirmPassword}
            helperText={errors.confirmPassword?.message}
            {...register("confirmPassword", {
              required: "Please confirm your password",
              validate: (value) =>
                value === getValues("password") || "Passwords do not match",
            })}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="toggle confirm password visibility"
                    onClick={toggleConfirmPasswordVisibility}
                    edge="end"
                  >
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={isPending}
            sx={{
              mt: 3,
              mb: 2,
              py: 1.5,
              textTransform: "none",
              fontSize: "1rem",
            }}
          >
            {isPending ? <CircularProgress size={24} /> : "Sign Up"}
          </Button>

          <Box className="text-center mt-4">
            <Typography variant="body2" className="text-gray-600">
              Already have an account?{" "}
              <Link
                to="/login"
                className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
              >
                Sign in
              </Link>
            </Typography>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default Register;
