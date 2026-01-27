import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8765',
        ws: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 600, // Increase warning limit slightly
    rollupOptions: {
      output: {
        manualChunks: {
          // Core vendor chunks
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-query': ['@tanstack/react-query'],
          'vendor-ui': ['lucide-react', 'clsx'],
          'vendor-markdown': ['react-markdown', 'remark-gfm'],
          'vendor-dates': ['date-fns'],
          // Split pages into separate chunks
          'page-chat': ['./src/components/chat/ChatPage.tsx'],
          'page-bench': ['./src/components/bench/BenchPage.tsx'],
          'page-bmad': ['./src/components/bmad/BMADPage.tsx'],
          'page-files': ['./src/components/files/FilesPage.tsx'],
          'page-watch': ['./src/components/watch/WatchPage.tsx'],
          'page-settings': ['./src/components/settings/SettingsPage.tsx'],
        }
      }
    }
  }
})
