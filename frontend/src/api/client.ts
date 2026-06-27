import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";

export type { AxiosError };

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let refreshQueue: ((token: string) => void)[] = [];

function clearAuthAndRedirect() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_refresh_token");
  localStorage.removeItem("auth_role");
  localStorage.removeItem("auth_admin_permission");
  window.location.href = "/login";
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (status === 401 && !original._retry && localStorage.getItem("auth_refresh_token")) {
      original._retry = true;

      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push((newToken: string) => {
            original.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(original));
          });
        });
      }

      isRefreshing = true;
      try {
        const refreshToken = localStorage.getItem("auth_refresh_token")!;
        const { data } = await axios.post("/api/auth/refresh", { refresh_token: refreshToken });

        localStorage.setItem("auth_token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("auth_refresh_token", data.refresh_token);
        }

        refreshQueue.forEach((cb) => cb(data.access_token));
        refreshQueue = [];

        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        clearAuthAndRedirect();
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    if (status === 401 && !localStorage.getItem("auth_refresh_token")) {
      clearAuthAndRedirect();
    } else if (status === 403 && localStorage.getItem("auth_token")) {
      clearAuthAndRedirect();
    }

    return Promise.reject(error);
  }
);

export function getErrorMessage(err: unknown, fallback = "Something went wrong."): string {
  const axiosErr = err as AxiosError<{ detail?: string }>;
  return axiosErr?.response?.data?.detail ?? fallback;
}

export default api;
