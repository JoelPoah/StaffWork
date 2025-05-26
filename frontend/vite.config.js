// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // necessary to bind to external IP in Codespaces
    port: 3000,       // or any available port
    strictPort: true, // avoid random fallback ports
  }
})
