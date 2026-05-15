import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

// In Docker the backend is reachable at http://backend:8000 (service name).
// Outside Docker (local dev) it is at http://localhost:8000.
const BACKEND_URL = process.env.VITE_BACKEND_URL || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    port: 5173,
    strictPort: false,
    host: true,   // bind to 0.0.0.0 so Docker can expose the port
    proxy: {
      // All /api/* requests are forwarded to FastAPI.
      // The /api prefix is stripped before forwarding:
      //   /api/auth/login  →  http://backend:8000/auth/login  (Docker)
      //   /api/auth/login  →  http://localhost:8000/auth/login (local)
      "/api": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },

  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setupTests.ts"],
  },
});
