import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  css: {
    preprocessorOptions: {
      // sass carbon dibaca dari node_modules, peringatan deprecation milik library sendiri tidak relevan untuk aplikasi
      scss: { loadPaths: [path.resolve(__dirname, 'node_modules')], quietDeps: true },
    },
  },
})
