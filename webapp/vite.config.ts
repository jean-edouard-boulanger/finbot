import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  base: "/finbot/",
  resolve: {
    alias: {
      components: path.resolve(__dirname, "src/components"),
      contexts: path.resolve(__dirname, "src/contexts"),
      routes: path.resolve(__dirname, "src/routes"),
      clients: path.resolve(__dirname, "src/clients"),
      utils: path.resolve(__dirname, "src/utils"),
      assets: path.resolve(__dirname, "src/assets"),
      hooks: path.resolve(__dirname, "src/hooks"),
      lib: path.resolve(__dirname, "src/lib"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5005,
    proxy: {
      "/api/v1": {
        target: "http://127.0.0.1:5003",
        changeOrigin: true,
      },
    },
  },
});
