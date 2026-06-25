import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api 요청은 FastAPI(8000)로 프록시 → 프론트는 상대경로만 쓰면 됨
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
