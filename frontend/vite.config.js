import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  esbuild: {
    loader: 'jsx',
    include: /src\/.*\.[jt]sx?$/,
    exclude: []
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: { '.js': 'jsx', '.jsx': 'jsx' }
    }
  },
  server: { port: 3000, host: true },
  build: { outDir: 'build' }
})
