import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      }
    }
  },
  build: {
    // Suppress chunk size warning — expected for Vue + Chart.js + Bootstrap bundle
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor JS libraries into separate cached chunks
          'vendor-vue': ['vue', 'vue-router', 'pinia'],
          'vendor-chart': ['chart.js', 'vue-chartjs'],
          'vendor-http': ['axios']
        }
      }
    }
  }
})

