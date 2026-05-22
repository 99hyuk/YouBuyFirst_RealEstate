import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';

const frontRoot = fileURLToPath(new URL('.', import.meta.url));
const stockDetailCopyAssets = 'C:/agents/YouBuyFirst/docs/assets/stock-detail-copy';

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    },
    fs: {
      allow: [frontRoot, stockDetailCopyAssets]
    }
  },
  test: {
    environment: 'jsdom',
    globals: true
  }
});
