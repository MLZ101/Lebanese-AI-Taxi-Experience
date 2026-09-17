import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Talk to FastAPI without thinking about CORS in dev.
    proxy: {
      "/game": "http://127.0.0.1:8000",
      "/ai": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
});
