import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiProxyTarget = env.VITE_API_PROXY_TARGET;

  return {
    server: {
      port: 2003,
      host: '0.0.0.0',
      proxy: apiProxyTarget
        ? {
            '/api': {
              target: apiProxyTarget,
              changeOrigin: true,
              ws: true,
            },
            '/uploads': {
              target: apiProxyTarget,
              changeOrigin: true,
            },
          }
        : undefined,
    },
    test: {
      environment: 'node',
    },
  };
});
