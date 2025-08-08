import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/admin':  { target: 'http://localhost:5010', changeOrigin: true },
      '/logout': { target: 'http://localhost:5010', changeOrigin: true },
    },
  },
});
