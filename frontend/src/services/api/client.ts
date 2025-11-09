import axios from "axios";
import { authStore } from "../../store/auth-store";

const baseURL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "") ?? "/api";

export const apiClient = axios.create({
  baseURL,
  withCredentials: false,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = authStore.getState().token;
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const { clearSession } = authStore.getState();
      clearSession();
    }
    return Promise.reject(error);
  }
);

