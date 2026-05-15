import axios from "axios";
import type { AxiosError } from "axios";

export type { AxiosError };

const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach the stored Bearer token to every outgoing request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Track consecutive 401s — only logout after 5 in a row to survive
// transient backend restarts or brief Docker network issues.
// StrictMode is disabled, but keep a generous threshold for any concurrent requests.
let consecutive401s = 0;
let logoutScheduled = false;

api.interceptors.response.use(
  (response) => {
    consecutive401s = 0; // reset on any success
    return response;
  },
  (error: AxiosError) => {
    const status = error.response?.status;

    if (status === 401 && localStorage.getItem("auth_token")) {
      consecutive401s++;
      if (consecutive401s >= 5 && !logoutScheduled) {
        // Five consecutive 401s means the token is genuinely expired/invalid
        logoutScheduled = true;
        consecutive401s = 0;
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_role");
        window.location.href = "/login";
      }
    } else if (status === 403 && localStorage.getItem("auth_token")) {
      // 403 on an authenticated request means role mismatch — the stored token
      // belongs to a different role than what auth_role says. Clear and re-login.
      if (!logoutScheduled) {
        logoutScheduled = true;
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_role");
        window.location.href = "/login";
      }
    } else {
      consecutive401s = 0;
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(err: unknown, fallback = "Something went wrong."): string {
  const axiosErr = err as AxiosError<{ detail?: string }>;
  return axiosErr?.response?.data?.detail ?? fallback;
}

export default api;
