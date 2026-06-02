import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    env: {
      VITE_API_BASE_URL: 'http://127.0.0.1:8001/api',
      VITE_CLIENT_ID: 'h5-web',
    },
  },
});
