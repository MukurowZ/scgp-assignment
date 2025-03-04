import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import VitePluginPug from 'vite-plugin-pug'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    VitePluginPug(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    warmup: {
      clientFiles: ['./src/views/*.vue', './src/components/*.vue', './src/App.vue', './src/router/*'],
    },
    hmr: {
      protocol: 'ws',
      host: 'localhost',
    },
  },
})
