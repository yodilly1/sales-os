import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Prospect Research Page Object
 *
 * Handles interactions with the prospect enrichment page.
 * Used for Prospect enrichment → CRM sync flow testing.
 */
export class ProspectPage extends BasePage {
  // Page elements
  readonly addProspectButton: Locator;
  readonly importButton: Locator;
  readonly prospectList: Locator;
  readonly prospectItem: Locator;
  readonly searchInput: Locator;
  readonly filterButton: Locator;

  // Form elements
  readonly firstNameInput: Locator;
  readonly lastNameInput: Locator;
  readonly emailInput: Locator;
  readonly companyInput: Locator;
  readonly titleInput: Locator;
  readonly phoneInput: Locator;
  readonly linkedInInput: Locator;
  readonly saveProspectButton: Locator;

  // Enrichment elements
  readonly enrichButton: Locator;
  readonly enrichmentResults: Locator;
  readonly verifiedBadge: Locator;
  readonly companyInsights: Locator;
  readonly socialProfiles: Locator;

  // CRM sync elements
  readonly syncToCrmButton: Locator;
  readonly crmStatusBadge: Locator;
  readonly hubspotSyncButton: Locator;
  readonly salesforceSyncButton: Locator;

  // Bulk actions
  readonly selectAllCheckbox: Locator;
  readonly bulkEnrichButton: Locator;
  readonly bulkSyncButton: Locator;

  constructor(page: Page) {
    super(page);

    // Main elements
    this.addProspectButton = page.locator('[data-testid="add-prospect-btn"]');
    this.importButton = page.locator('[data-testid="import-prospects-btn"]');
    this.prospectList = page.locator('[data-testid="prospect-list"]');
    this.prospectItem = page.locator('[data-testid="prospect-item"]');
    this.searchInput = page.locator('[data-testid="prospect-search-input"]');
    this.filterButton = page.locator('[data-testid="prospect-filter-btn"]');

    // Form elements
    this.firstNameInput = page.locator('[data-testid="prospect-firstname-input"]');
    this.lastNameInput = page.locator('[data-testid="prospect-lastname-input"]');
    this.emailInput = page.locator('[data-testid="prospect-email-input"]');
    this.companyInput = page.locator('[data-testid="prospect-company-input"]');
    this.titleInput = page.locator('[data-testid="prospect-title-input"]');
    this.phoneInput = page.locator('[data-testid="prospect-phone-input"]');
    this.linkedInInput = page.locator('[data-testid="prospect-linkedin-input"]');
    this.saveProspectButton = page.locator('[data-testid="save-prospect-btn"]');

    // Enrichment elements
    this.enrichButton = page.locator('[data-testid="enrich-prospect-btn"]');
    this.enrichmentResults = page.locator('[data-testid="enrichment-results"]');
    this.verifiedBadge = page.locator('[data-testid="verified-badge"]');
    this.companyInsights = page.locator('[data-testid="company-insights"]');
    this.socialProfiles = page.locator('[data-testid="social-profiles"]');

    // CRM sync elements
    this.syncToCrmButton = page.locator('[data-testid="sync-to-crm-btn"]');
    this.crmStatusBadge = page.locator('[data-testid="crm-status-badge"]');
    this.hubspotSyncButton = page.locator('[data-testid="hubspot-sync-btn"]');
    this.salesforceSyncButton = page.locator('[data-testid="salesforce-sync-btn"]');

    // Bulk actions
    this.selectAllCheckbox = page.locator('[data-testid="select-all-prospects"]');
    this.bulkEnrichButton = page.locator('[data-testid="bulk-enrich-btn"]');
    this.bulkSyncButton = page.locator('[data-testid="bulk-sync-btn"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('/prospects');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to a specific prospect
   */
  async gotoProspect(id: string): Promise<void> {
    await this.page.goto(`/prospects/${id}`);
    await this.waitForPageLoad();
  }

  /**
   * Start adding a new prospect
   */
  async startAddProspect(): Promise<void> {
    await this.addProspectButton.click();
    await this.page.waitForURL(/\/prospects\/new/);
  }

  /**
   * Fill prospect form
   */
  async fillProspectForm(prospect: {
    firstName: string;
    lastName: string;
    email: string;
    company: string;
    title?: string;
    phone?: string;
    linkedIn?: string;
  }): Promise<void> {
    await this.fillField(this.firstNameInput, prospect.firstName);
    await this.fillField(this.lastNameInput, prospect.lastName);
    await this.fillField(this.emailInput, prospect.email);
    await this.fillField(this.companyInput, prospect.company);

    if (prospect.title) {
      await this.fillField(this.titleInput, prospect.title);
    }

    if (prospect.phone) {
      await this.fillField(this.phoneInput, prospect.phone);
    }

    if (prospect.linkedIn) {
      await this.fillField(this.linkedInInput, prospect.linkedIn);
    }
  }

  /**
   * Save prospect
   */
  async saveProspect(): Promise<void> {
    await this.saveProspectButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Enrich prospect data
   */
  async enrichProspect(): Promise<void> {
    await this.enrichButton.click();
    await this.waitForLoadingComplete();
    // Wait for enrichment results
    await this.enrichmentResults.waitFor({ state: 'visible', timeout: 30000 });
  }

  /**
   * Sync prospect to CRM
   */
  async syncToCrm(): Promise<void> {
    await this.syncToCrmButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Sync to HubSpot specifically
   */
  async syncToHubspot(): Promise<void> {
    await this.hubspotSyncButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Verify prospect is enriched
   */
  async verifyProspectEnriched(): Promise<void> {
    await expect(this.enrichmentResults).toBeVisible();
    await expect(this.verifiedBadge).toBeVisible();
  }

  /**
   * Verify CRM sync status
   */
  async verifyCrmSyncStatus(status: 'synced' | 'pending' | 'error'): Promise<void> {
    await expect(this.crmStatusBadge).toBeVisible();
    await expect(this.crmStatusBadge).toHaveAttribute('data-status', status);
  }

  /**
   * Search for prospects
   */
  async searchProspects(query: string): Promise<void> {
    await this.fillField(this.searchInput, query);
    await this.page.keyboard.press('Enter');
    await this.waitForLoadingComplete();
  }

  /**
   * Get number of prospects in list
   */
  async getProspectCount(): Promise<number> {
    return await this.prospectItem.count();
  }

  /**
   * Select a prospect from the list
   */
  async selectProspect(index: number): Promise<void> {
    await this.prospectItem.nth(index).click();
    await this.waitForLoadingComplete();
  }

  /**
   * Bulk select all prospects
   */
  async selectAllProspects(): Promise<void> {
    await this.selectAllCheckbox.check();
  }

  /**
   * Bulk enrich selected prospects
   */
  async bulkEnrich(): Promise<void> {
    await this.bulkEnrichButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Bulk sync selected prospects to CRM
   */
  async bulkSync(): Promise<void> {
    await this.bulkSyncButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Get enrichment data
   */
  async getEnrichmentData(): Promise<{
    verified: boolean;
    companyInsights: string;
    socialProfiles: string;
  }> {
    const verified = await this.verifiedBadge.isVisible();
    const insights = await this.getText(this.companyInsights);
    const profiles = await this.getText(this.socialProfiles);

    return {
      verified,
      companyInsights: insights,
      socialProfiles: profiles,
    };
  }

  /**
   * Import prospects from file
   */
  async importProspects(filePath: string): Promise<void> {
    await this.importButton.click();
    const fileInput = this.page.locator('[data-testid="import-file-input"]');
    await fileInput.setInputFiles(filePath);
    await this.waitForLoadingComplete();
  }
}
