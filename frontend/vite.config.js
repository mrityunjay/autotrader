import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isGHPages = process.env.GITHUB_PAGES === 'true'

export default defineConfig({
  plugins: [react()],
  // Base path for GitHub Pages: /autotrader/
  base: isGHPages ? '/autotrader/' : '/',
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
})
