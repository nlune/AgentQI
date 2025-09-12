import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/v1': {
        target: proxyTarget,
        changeOrigin: true,
      },
      '/pdfs': {
        target: proxyTarget,
        changeOrigin: true,
      },
    },
  },
})
