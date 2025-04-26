import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    cors: true
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
