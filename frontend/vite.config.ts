// React + Tailwind/shadcn tooling alongside the existing LearnPlay CSS.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: { proxy: { '/api': { target: process.env.API_PROXY_TARGET ?? 'http://localhost:5000', changeOrigin: false } } },
})
