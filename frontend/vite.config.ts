// TypeScript / frontend/vite.config.ts / Node 24 + Vite 8 / descomplica cursos web client
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': { target: process.env.API_PROXY_TARGET ?? 'http://localhost:5000', changeOrigin: false } } },
})
