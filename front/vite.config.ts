import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';

import { resolveBackendProxyTarget } from './src/lib/backend-proxy-target';

const frontRoot = fileURLToPath(new URL('.', import.meta.url));
const backendProxyTarget = resolveBackendProxyTarget(process.env);

export default defineConfig({
  plugins: [vue()],
  server: {
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      '/api': {
        target: backendProxyTarget,
        changeOrigin: true
      }
    },
    fs: {
      allow: [frontRoot]
    }
  },
  test: {
    environment: 'jsdom',
    globals: true
  }
});
