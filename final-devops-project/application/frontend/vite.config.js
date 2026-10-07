import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In development `npm run dev` proxies /api to a backend on :8000, mirroring what
// nginx (Docker) and the Ingress (Kubernetes) do in the deployed environments.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': process.env.VITE_API_TARGET || 'http://localhost:8000' },
  },
  build: { sourcemap: false },
});
