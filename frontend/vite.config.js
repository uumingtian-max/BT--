import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiUrl = env.REACT_APP_API_URL || 'http://localhost:8000';

  return {
    plugins: [react({ include: /\.(jsx|js)$/ })],
    esbuild: {
      loader: 'jsx',
      include: /src\/.*\.jsx?$/,
      exclude: [],
    },
    optimizeDeps: {
      esbuildOptions: {
        loader: { '.js': 'jsx' },
      },
    },
    build: {
      outDir: 'build',
      emptyOutDir: true,
    },
    server: {
      port: 3000,
      proxy: {
        '/chat': apiUrl,
        '/agent': apiUrl,
        '/meta': apiUrl,
        '/observe': apiUrl,
        '/notebook': apiUrl,
        '/scheduler': apiUrl,
        '/gateway': apiUrl,
        '/mcp': apiUrl,
        '/health': apiUrl,
        '/outputs': apiUrl,
        '/upload_file': apiUrl,
      },
    },
    base: './',
    define: {
      'process.env.REACT_APP_API_URL': JSON.stringify(apiUrl),
    },
  };
});
