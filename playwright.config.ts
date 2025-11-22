import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for Sales OS E2E Testing
 *
 * This configuration supports:
 * - Multiple browser testing (Chromium, Firefox, WebKit)
 * - Parallel test execution
 * - Screenshot and video capture on failure
 * - Test retries for flaky tests
 * - HTML and JSON coverage reporting
 */

export default defineConfig({
  // Test directory
  testDir: './frontend/tests/e2e',

  // Test file pattern
  testMatch: '**/*.spec.ts',

  // Maximum time per test
  timeout: 30000,

  // Expect timeout
  expect: {
    timeout: 5000,
  },

  // Run tests in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry failed tests (2 retries on CI, 0 locally for faster feedback)
  retries: process.env.CI ? 2 : 0,

  // Parallel workers (reduce on CI to avoid resource issues)
  workers: process.env.CI ? 2 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results/e2e-results.json' }],
    ['list'],
    ...(process.env.CI ? [['github' as const]] : []),
  ],

  // Shared settings for all projects
  use: {
    // Base URL for tests
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',

    // Collect trace on first retry
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'on-first-retry',

    // Viewport size
    viewport: { width: 1280, height: 720 },

    // Navigation timeout
    navigationTimeout: 10000,

    // Action timeout
    actionTimeout: 10000,
  },

  // Projects for different browsers
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Mobile viewports
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // Web server configuration (start Next.js dev server before tests)
  webServer: {
    command: 'npm run dev',
    cwd: './frontend',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },

  // Output directory for test artifacts
  outputDir: 'test-results',

  // Global setup and teardown
  globalSetup: './frontend/tests/e2e/global-setup.ts',
  globalTeardown: './frontend/tests/e2e/global-teardown.ts',
});
