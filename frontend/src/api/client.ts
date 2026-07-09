import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";

export type { AxiosError };

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
  // Required so the browser sends HttpOnly auth cookies on every request.
  withCredentials: true,
});

// Read the non-HttpOnly csrf_token cookie that the backend sets on every response.
function getCsrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

// Attach CSRF token to every state-changing request (browser cookie-auth flow).
// Bearer-authenticated requests (API clients) don't need this — the backend
// skips CSRF validation when an Authorization header is present.
api.interceptors.request.use((config) => {
  const method = config.method?.toLowerCase() ?? "";
  if (["post", "put", "patch", "delete"].includes(method)) {
    const token = getCsrfToken();
    if (token) config.headers["X-CSRF-Token"] = token;
  }
  return config;
});

let isRefreshing = false;
let refreshQueue: ((ok: boolean) => void)[] = [];

function clearAuthAndRedirect() {
  localStorage.removeItem("auth_role");
  localStorage.removeItem("auth_admin_permission");
  window.location.href = "/login";
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status  = error.response?.status;
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // On 401, try a silent token refresh using the HttpOnly refresh cookie.
    if (status === 401 && !original._retry) {
      original._retry = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push((ok) => (ok ? resolve(api(original)) : reject(error)));
        });
      }

      isRefreshing = true;
      try {
        // Browser sends the refresh_token cookie automatically — no body needed.
        await axios.post("/api/v1/auth/refresh", {}, {
          withCredentials: true,
          headers: { "X-CSRF-Token": getCsrfToken() },
        });
        refreshQueue.forEach((cb) => cb(true));
        refreshQueue = [];
        return api(original);
      } catch {
        refreshQueue.forEach((cb) => cb(false));
        refreshQueue = [];
        clearAuthAndRedirect();
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    if (status === 403 && localStorage.getItem("auth_role")) {
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
