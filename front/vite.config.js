import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"

export default defineConfig({
  plugins: [vue()],
  publicDir: "../static",
  server: {
    host: "0.0.0.0",
    port: 9919,
    strictPort: true,
    hmr: {
      host: "localhost",
      clientPort: 9919,
      protocol: "ws",
    },
    watch: {
      usePolling: true,
      interval: 300,
    },
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true
      }
    }
  }
})
