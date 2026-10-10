import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development, `npm run dev` proxies /api to a locally running API.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://localhost:8000' },
  },
})
