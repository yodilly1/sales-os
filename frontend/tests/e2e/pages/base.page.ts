import { Page, Locator, expect } from '@playwright/test';

/**
 * Base Page Object
 *
 * Provides common functionality for all page objects.
 * All page objects should extend this class.
 */
export abstract class BasePage {
  readonly page: Page;

  // Common elements across all pages
  readonly header: Locator;
  readonly sidebar: Locator;
  readonly mainContent: Locator;
  readonly loadingSpinner: Locator;
  readonly notification: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.locator('header');
    this.sidebar = page.locator('[data-testid="sidebar"]');
    this.mainContent = page.locator('main');
    this.loadingSpinner = page.locator('[data-testid="loading-spinner"]');
    this.notification = page.locator('[data-testid="notification"]');
    this.errorMessage = page.locator('[data-testid="error-message"]');
  }

  /**
   * Navigate to the page URL
   */
  abstract goto(): Promise<void>;

  /**
   * Wait for the page to fully load
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
    await this.waitForLoadingComplete();
  }

  /**
   * Wait for loading spinner to disappear
   */
  async waitForLoadingComplete(): Promise<void> {
    // Wait for any loading spinners to disappear
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {
      // Loading spinner might not exist, which is fine
    });
  }

  /**
   * Check if notification is visible with expected text
   */
  async expectNotification(text: string): Promise<void> {
    await expect(this.notification).toBeVisible();
    await expect(this.notification).toContainText(text);
  }

  /**
   * Check if error message is visible with expected text
   */
  async expectError(text: string): Promise<void> {
    await expect(this.errorMessage).toBeVisible();
    await expect(this.errorMessage).toContainText(text);
  }

  /**
   * Take a screenshot with a descriptive name
   */
  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `test-results/screenshots/${name}.png`, fullPage: true });
  }

  /**
   * Click and wait for navigation
   */
  async clickAndWaitForNavigation(locator: Locator): Promise<void> {
    await Promise.all([
      this.page.waitForLoadState('networkidle'),
      locator.click(),
    ]);
  }

  /**
   * Fill form field with value
   */
  async fillField(locator: Locator, value: string): Promise<void> {
    await locator.clear();
    await locator.fill(value);
  }

  /**
   * Select option from dropdown
   */
  async selectOption(locator: Locator, value: string): Promise<void> {
    await locator.selectOption(value);
  }

  /**
   * Check if element is visible
   */
  async isVisible(locator: Locator): Promise<boolean> {
    return await locator.isVisible();
  }

  /**
   * Get text content from element
   */
  async getText(locator: Locator): Promise<string> {
    return (await locator.textContent()) || '';
  }
}
