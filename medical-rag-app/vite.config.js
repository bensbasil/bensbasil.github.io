import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/medical-rag-app-deploy/',
  build: {
    outDir: '../medical-rag-app-deploy',
    emptyOutDir: true
  }
})
