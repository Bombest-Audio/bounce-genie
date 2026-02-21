import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Tauri expects a fixed port in dev
  server: {
    port: 5173,
    strictPort: true,
  },
  clearScreen: false,
  envPrefix: ['VITE_', 'TAURI_'],
  build: {
    // Tauri uses Chromium under the hood
    target: 'chrome105',
  },
})
