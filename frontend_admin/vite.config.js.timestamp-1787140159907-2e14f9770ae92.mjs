// vite.config.js
import { defineConfig, loadEnv } from "file:///Users/jackbond/Desktop/Ghana_loan/GalaCredit/frontend_admin/node_modules/vite/dist/node/index.js";
import vue from "file:///Users/jackbond/Desktop/Ghana_loan/GalaCredit/frontend_admin/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import viteCompression from "file:///Users/jackbond/Desktop/Ghana_loan/GalaCredit/frontend_admin/node_modules/vite-plugin-compression/dist/index.mjs";
var vite_config_default = defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiProxyTarget = env.VITE_API_PROXY_TARGET;
  const proxy = apiProxyTarget ? {
    "/api": {
      target: apiProxyTarget,
      changeOrigin: true,
      ws: true
    }
  } : void 0;
  return {
    plugins: [
      vue(),
      viteCompression({
        algorithm: "gzip",
        ext: ".gz",
        threshold: 10240
      })
    ],
    server: {
      port: 2002,
      strictPort: true,
      host: "0.0.0.0",
      proxy
    }
  };
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvVXNlcnMvamFja2JvbmQvRGVza3RvcC9HaGFuYV9sb2FuL0dhbGFDcmVkaXQvZnJvbnRlbmRfYWRtaW5cIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIi9Vc2Vycy9qYWNrYm9uZC9EZXNrdG9wL0doYW5hX2xvYW4vR2FsYUNyZWRpdC9mcm9udGVuZF9hZG1pbi92aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vVXNlcnMvamFja2JvbmQvRGVza3RvcC9HaGFuYV9sb2FuL0dhbGFDcmVkaXQvZnJvbnRlbmRfYWRtaW4vdml0ZS5jb25maWcuanNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcsIGxvYWRFbnYgfSBmcm9tICd2aXRlJ1xuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXG5pbXBvcnQgdml0ZUNvbXByZXNzaW9uIGZyb20gJ3ZpdGUtcGx1Z2luLWNvbXByZXNzaW9uJ1xuXG4vLyBodHRwczovL3ZpdGVqcy5kZXYvY29uZmlnL1xuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKCh7IG1vZGUgfSkgPT4ge1xuICBjb25zdCBlbnYgPSBsb2FkRW52KG1vZGUsIHByb2Nlc3MuY3dkKCksICcnKVxuICBjb25zdCBhcGlQcm94eVRhcmdldCA9IGVudi5WSVRFX0FQSV9QUk9YWV9UQVJHRVRcbiAgY29uc3QgcHJveHkgPSBhcGlQcm94eVRhcmdldFxuICAgID8ge1xuICAgICAgICAnL2FwaSc6IHtcbiAgICAgICAgICB0YXJnZXQ6IGFwaVByb3h5VGFyZ2V0LFxuICAgICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZSxcbiAgICAgICAgICB3czogdHJ1ZVxuICAgICAgICB9XG4gICAgICB9XG4gICAgOiB1bmRlZmluZWRcblxuICByZXR1cm4ge1xuICAgIHBsdWdpbnM6IFtcbiAgICAgIHZ1ZSgpLFxuICAgICAgdml0ZUNvbXByZXNzaW9uKHtcbiAgICAgICAgYWxnb3JpdGhtOiAnZ3ppcCcsXG4gICAgICAgIGV4dDogJy5neicsXG4gICAgICAgIHRocmVzaG9sZDogMTAyNDBcbiAgICAgIH0pXG4gICAgXSxcbiAgICBzZXJ2ZXI6IHtcbiAgICAgIHBvcnQ6IDIwMDIsXG4gICAgICBzdHJpY3RQb3J0OiB0cnVlLFxuICAgICAgaG9zdDogJzAuMC4wLjAnLFxuICAgICAgcHJveHlcbiAgICB9XG4gIH1cbn0pXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQXNXLFNBQVMsY0FBYyxlQUFlO0FBQzVZLE9BQU8sU0FBUztBQUNoQixPQUFPLHFCQUFxQjtBQUc1QixJQUFPLHNCQUFRLGFBQWEsQ0FBQyxFQUFFLEtBQUssTUFBTTtBQUN4QyxRQUFNLE1BQU0sUUFBUSxNQUFNLFFBQVEsSUFBSSxHQUFHLEVBQUU7QUFDM0MsUUFBTSxpQkFBaUIsSUFBSTtBQUMzQixRQUFNLFFBQVEsaUJBQ1Y7QUFBQSxJQUNFLFFBQVE7QUFBQSxNQUNOLFFBQVE7QUFBQSxNQUNSLGNBQWM7QUFBQSxNQUNkLElBQUk7QUFBQSxJQUNOO0FBQUEsRUFDRixJQUNBO0FBRUosU0FBTztBQUFBLElBQ0wsU0FBUztBQUFBLE1BQ1AsSUFBSTtBQUFBLE1BQ0osZ0JBQWdCO0FBQUEsUUFDZCxXQUFXO0FBQUEsUUFDWCxLQUFLO0FBQUEsUUFDTCxXQUFXO0FBQUEsTUFDYixDQUFDO0FBQUEsSUFDSDtBQUFBLElBQ0EsUUFBUTtBQUFBLE1BQ04sTUFBTTtBQUFBLE1BQ04sWUFBWTtBQUFBLE1BQ1osTUFBTTtBQUFBLE1BQ047QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
