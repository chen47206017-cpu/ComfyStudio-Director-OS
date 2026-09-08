import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/director/',
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 8191,
    strictPort: false,
  },
  build: {
    outDir: '../ui/dist',
    emptyOutDir: false,
    sourcemap: true,
  },
})
