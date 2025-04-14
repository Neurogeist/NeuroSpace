import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

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
            // Add X-User-Address header
            proxyReq.setHeader('X-User-Address', '0x1234567890123456789012345678901234567890');
            
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
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    'process.env': {
      REACT_APP_PAYMENT_CONTRACT_ADDRESS: process.env.REACT_APP_PAYMENT_CONTRACT_ADDRESS
    }
  }
})
