import axios, { AxiosError } from "axios";
import type { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { API_CONFIG } from "../app/config/api";
import { getAccessToken, setAccessToken, clearAccessToken } from "../features/auth/context/authService";
const api: AxiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});
let isRefreshing = false;

api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest?._retry) {
      if (originalRequest) originalRequest._retry = true;

      if (isRefreshing) {
        try {
          return api(originalRequest);
        } catch (e) {
          return Promise.reject(e);
        }
      }

      isRefreshing = true;
      try {
        const resp = await api.post(API_CONFIG.ENDPOINTS.AUTH.REFRESH);
        const newToken = resp.data?.token?.access_token ?? null;
        if (newToken) {
          setAccessToken(newToken);
        }

        isRefreshing = false;

        if (originalRequest) return api(originalRequest);
      } catch (refreshError: any) {
        isRefreshing = false;
        if (refreshError?.response?.status === 401) {
          clearAccessToken();
          window.location.href = "/login";
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  },
);

export default api;
