import { defineConfig, devices } from '@playwright/test'
const port = process.env.E2E_PORT ?? '15173'
const baseURL = 'http://127.0.0.1:' + port
export default defineConfig({
  testDir: './tests/e2e', fullyParallel: false, workers: 1, reporter: 'list', timeout: 30000,
  use: { baseURL, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], channel: 'chrome', viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium', channel: 'chrome' } },
  ],
  webServer: [
    { command: 'node ../scripts/browser-scraper-fixtures.mjs', url: 'http://127.0.0.1:18000/health', reuseExistingServer: false },
    { command: 'java -jar ../backend/target/payment-optimizer-0.0.1-SNAPSHOT.jar', url: 'http://127.0.0.1:18080/actuator/health', reuseExistingServer: false, timeout: 60000,
      env: { PORT: '18080', SPRING_PROFILES_ACTIVE: 'local', SCRAPER_BASE_URL: 'http://127.0.0.1:18000', CORS_ALLOWED_ORIGINS: baseURL } },
    { command: 'npm run dev -- --port ' + port + ' --strictPort', url: baseURL, reuseExistingServer: false,
      env: { VITE_API_BASE_URL: 'http://127.0.0.1:18080' } },
  ],
})
