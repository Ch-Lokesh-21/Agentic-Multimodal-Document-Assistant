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
import { useLogin } from "../hooks/index.ts";
import type { UserLoginRequest } from "../types/index.ts"
import { handleSuccess } from "../../../utils/errorHandler.ts";

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { mutate: login, isPending } = useLogin();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UserLoginRequest>({
    mode: "onBlur",
  });

  const onSubmit = (data: UserLoginRequest) => {
    login(data, {
      onSuccess: () => {
        handleSuccess("Logged in successfully!");
        navigate("/chat");
      },
    });
  };

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
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
          Welcome Back
        </Typography>
        <Typography variant="body2" className="text-center text-gray-600 mb-6">
          Sign in to continue to your account
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
            autoComplete="current-password"
            error={!!errors.password}
            helperText={errors.password?.message}
            {...register("password", {
              required: "Password is required",
              minLength: {
                value: 8,
                message: "Password must be at least 8 characters",
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
            {isPending ? <CircularProgress size={24} /> : "Sign In"}
          </Button>

          <Box className="text-center mt-4">
            <Typography variant="body2" className="text-gray-600">
              Don't have an account?{" "}
              <Link
                to="/register"
                className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
              >
                Sign up
              </Link>
            </Typography>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default Login;
