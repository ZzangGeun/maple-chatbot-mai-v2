import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // 개발 서버에서는 '/', 빌드 시에는 '/static/dist/' 사용
  base: command === 'serve' ? '/' : '/static/dist/',
  server: {
    // ngrok 터널 등 외부 호스트 접속 허용
    allowedHosts: true,
    // /api 경로만 Django 백엔드로 프록시합니다.
    // /chat, /character 등 페이지 경로는 React Router가 처리하므로 프록시하지 않습니다.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/admin': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
    manifest: true,
  },
  // Vitest 설정: 속성 기반 테스트(fast-check) 및 렌더/상호작용
  // 테스트(@testing-library/react)를 위한 jsdom 환경
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    css: true,
    include: ['src/**/*.{test,spec}.{js,jsx}'],
  }
}))
