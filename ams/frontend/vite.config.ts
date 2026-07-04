import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Performance budget (Section 14.6): route-level code splitting keeps the
// critical path <= 300 KB gz; CI Lighthouse budget enforces regressions.
export default defineConfig({
  plugins: [react()],
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          mui: ['@mui/material'],
          query: ['@tanstack/react-query'],
        },
      },
    },
  },
  server: {
    proxy: {
      '/v1': { target: 'http://localhost:5080', changeOrigin: true },
    },
  },
});
