import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  define: { 'import.meta.env.VITE_API_BASE_URL': JSON.stringify('') },
  test: { environment: 'jsdom', include: ['tests/react/**/*.test.{ts,tsx}'], setupFiles: ['tests/react/setup.ts'] },
})
