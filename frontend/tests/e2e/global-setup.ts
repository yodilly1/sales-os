import { FullConfig } from '@playwright/test';

/**
 * Global Setup for Playwright E2E Tests
 *
 * This runs once before all tests to:
 * - Set up test environment
 * - Initialize test database state
 * - Configure authentication tokens
 */
async function globalSetup(config: FullConfig): Promise<void> {
  console.log('\n🚀 Starting E2E test suite...');
  console.log(`📌 Base URL: ${config.projects[0]?.use?.baseURL || 'http://localhost:3000'}`);

  // Set up environment variables for testing
  process.env.NODE_ENV = 'test';
  process.env.NEXT_PUBLIC_API_URL = process.env.E2E_API_URL || 'http://localhost:8000';

  // Initialize test database if needed
  if (process.env.E2E_RESET_DB === 'true') {
    console.log('🗄️  Resetting test database...');
    // Database reset logic would go here
    // await resetTestDatabase();
  }

  // Set up authentication state if needed
  if (process.env.E2E_AUTH_REQUIRED === 'true') {
    console.log('🔐 Setting up authentication...');
    // Authentication setup would go here
    // await setupTestAuth();
  }

  console.log('✅ Global setup complete\n');
}

export default globalSetup;
