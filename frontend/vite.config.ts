import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // Forward all headers from the original request
            const headers = req.headers;
            Object.keys(headers).forEach(key => {
              const value = headers[key];
              if (value !== undefined) {
                proxyReq.setHeader(key, value);
              }
            });
          });
        }
      }
    }
  }
})
