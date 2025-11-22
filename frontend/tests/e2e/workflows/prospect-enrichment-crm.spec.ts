import { test, expect } from '../fixtures';
import { ProspectPage } from '../pages';
import { setupApiMocks, ApiMock } from '../mocks/api.mock';

/**
 * E2E Test Suite: Prospect Enrichment → CRM Sync Flow
 *
 * Tests the complete workflow from adding prospects,
 * enriching their data, to syncing with CRM.
 *
 * Core workflow:
 * 1. Add prospect (name, title, company, email)
 * 2. Enrich prospect data
 * 3. Verify enrichment results
 * 4. Sync to CRM (HubSpot)
 */

test.describe('Prospect Enrichment → CRM Sync Flow', () => {
  let prospectPage: ProspectPage;
  let apiMock: ApiMock;

  test.beforeEach(async ({ authenticatedPage }) => {
    prospectPage = new ProspectPage(authenticatedPage);
    apiMock = await setupApiMocks(authenticatedPage);
  });

  test.afterEach(async () => {
    await apiMock.clearMocks();
  });

  test.describe('Prospect List', () => {
    test('should display existing prospects', async () => {
      await prospectPage.goto();

      // Verify prospect list is visible
      await expect(prospectPage.prospectList).toBeVisible();

      // Should show existing prospects
      const count = await prospectPage.getProspectCount();
      expect(count).toBeGreaterThan(0);
    });

    test('should search for prospects', async () => {
      await prospectPage.goto();

      // Search for specific prospect
      await prospectPage.searchProspects('John');

      // Results should be filtered
      await prospectPage.waitForLoadingComplete();
      const items = await prospectPage.prospectItem.all();

      for (const item of items) {
        const text = await item.textContent();
        expect(text?.toLowerCase()).toContain('john');
      }
    });

    test('should filter prospects by verification status', async ({ authenticatedPage }) => {
      await prospectPage.goto();

      // Click filter button
      await prospectPage.filterButton.click();

      // Select verified only
      const verifiedFilter = authenticatedPage.locator('[data-testid="filter-verified"]');
      await verifiedFilter.click();

      // Wait for filter
      await prospectPage.waitForLoadingComplete();

      // All visible items should be verified
      const badges = await prospectPage.verifiedBadge.all();
      expect(badges.length).toBeGreaterThan(0);
    });
  });

  test.describe('Prospect Creation', () => {
    test('should add new prospect with basic info', async ({ mockData }) => {
      await prospectPage.goto();
      await prospectPage.startAddProspect();

      const prospect = mockData.prospect();

      await prospectPage.fillProspectForm({
        firstName: prospect.firstName,
        lastName: prospect.lastName,
        email: prospect.email,
        company: prospect.company,
        title: prospect.title,
      });

      await prospectPage.saveProspect();

      // Verify success
      await prospectPage.expectNotification('Prospect created');
    });

    test('should validate email format', async ({ authenticatedPage }) => {
      await prospectPage.goto();
      await prospectPage.startAddProspect();

      await prospectPage.fillProspectForm({
        firstName: 'Test',
        lastName: 'User',
        email: 'invalid-email',
        company: 'Test Corp',
      });

      await prospectPage.saveProspectButton.click();

      // Should show email validation error
      const emailError = authenticatedPage.locator('[data-testid="email-error"]');
      await expect(emailError).toBeVisible();
      await expect(emailError).toContainText('valid email');
    });

    test('should detect duplicate prospects', async ({ authenticatedPage, mockData }) => {
      await prospectPage.goto();
      await prospectPage.startAddProspect();

      // Use email that already exists
      await prospectPage.fillProspectForm({
        firstName: 'John',
        lastName: 'Doe',
        email: 'john.doe@acme.com', // Existing email from mock
        company: 'Acme Corp',
      });

      await prospectPage.saveProspectButton.click();

      // Should show duplicate warning
      const duplicateWarning = authenticatedPage.locator('[data-testid="duplicate-warning"]');
      await expect(duplicateWarning).toBeVisible();
    });

    test('should add prospect with all optional fields', async ({ mockData }) => {
      await prospectPage.goto();
      await prospectPage.startAddProspect();

      const prospect = mockData.prospect();

      await prospectPage.fillProspectForm({
        firstName: prospect.firstName,
        lastName: prospect.lastName,
        email: prospect.email,
        company: prospect.company,
        title: prospect.title,
        phone: prospect.phone,
        linkedIn: prospect.linkedIn,
      });

      await prospectPage.saveProspect();
      await prospectPage.expectNotification('Prospect created');
    });
  });

  test.describe('Prospect Enrichment', () => {
    test('should enrich prospect data', async ({ mockData }) => {
      await prospectPage.goto();

      // Select first prospect
      await prospectPage.selectProspect(0);

      // Enrich the prospect
      await prospectPage.enrichProspect();

      // Verify enrichment results displayed
      await prospectPage.verifyProspectEnriched();
    });

    test('should display company insights after enrichment', async ({ authenticatedPage }) => {
      await prospectPage.goto();
      await prospectPage.selectProspect(0);
      await prospectPage.enrichProspect();

      // Company insights should be visible
      await expect(prospectPage.companyInsights).toBeVisible();

      const insights = await prospectPage.getText(prospectPage.companyInsights);
      expect(insights).toContain('Technology'); // Industry from mock
    });

    test('should display social profiles after enrichment', async ({ authenticatedPage }) => {
      await prospectPage.goto();
      await prospectPage.selectProspect(0);
      await prospectPage.enrichProspect();

      // Social profiles should be visible
      await expect(prospectPage.socialProfiles).toBeVisible();

      const profiles = await prospectPage.getText(prospectPage.socialProfiles);
      expect(profiles).toContain('linkedin');
    });

    test('should show verified badge after successful enrichment', async () => {
      await prospectPage.goto();
      await prospectPage.selectProspect(0);
      await prospectPage.enrichProspect();

      await expect(prospectPage.verifiedBadge).toBeVisible();
    });

    test('should handle enrichment failure gracefully', async ({ authenticatedPage }) => {
      await prospectPage.goto();

      // Mock enrichment failure
      await apiMock.mockError('/api/prospects/*/enrich', 400, 'Unable to find data for this prospect');

      await prospectPage.selectProspect(0);
      await prospectPage.enrichButton.click();

      // Should show error message
      await prospectPage.expectError('Unable to find data');
    });

    test('should show enrichment in progress indicator', async ({ authenticatedPage }) => {
      await prospectPage.goto();
      await prospectPage.selectProspect(0);

      // Start enrichment
      await prospectPage.enrichButton.click();

      // Progress indicator should appear
      const progressIndicator = authenticatedPage.locator('[data-testid="enrichment-progress"]');
      await expect(progressIndicator).toBeVisible();

      // Wait for completion
      await prospectPage.waitForLoadingComplete();
    });
  });

  test.describe('Bulk Operations', () => {
    test('should bulk select all prospects', async () => {
      await prospectPage.goto();

      await prospectPage.selectAllProspects();

      // All checkboxes should be checked
      const checkboxes = await prospectPage.page.locator('[data-testid="prospect-checkbox"]').all();
      for (const checkbox of checkboxes) {
        await expect(checkbox).toBeChecked();
      }
    });

    test('should bulk enrich multiple prospects', async ({ authenticatedPage }) => {
      await prospectPage.goto();

      // Select multiple prospects
      await prospectPage.selectAllProspects();

      // Bulk enrich
      await prospectPage.bulkEnrich();

      // Progress should show for bulk operation
      const bulkProgress = authenticatedPage.locator('[data-testid="bulk-enrich-progress"]');
      await expect(bulkProgress).toBeVisible();

      // Wait for completion
      await prospectPage.waitForLoadingComplete();
      await prospectPage.expectNotification('Enrichment complete');
    });

    test('should bulk sync to CRM', async ({ authenticatedPage }) => {
      await prospectPage.goto();

      await prospectPage.selectAllProspects();
      await prospectPage.bulkSync();

      // Wait for sync to complete
      await prospectPage.waitForLoadingComplete();
      await prospectPage.expectNotification('Synced to CRM');
    });
  });

  test.describe('CRM Sync', () => {
    test('should sync prospect to CRM', async () => {
      await prospectPage.goto();
      await prospectPage.selectProspect(0);

      // Enrich first to have data to sync
      await prospectPage.enrichProspect();

      // Sync to CRM
      await prospectPage.syncToCrm();

      // Verify success
      await prospectPage.expectNotification('Synced to CRM');
    });

    test('should sync to HubSpot specifically', async () => {
      await prospectPage.goto();
      await prospectPage.selectProspect(0);
      await prospectPage.enrichProspect();

      // Sync to HubSpot
      await prospectPage.syncToHubspot();

      await prospectPage.expectNotification('Synced to HubSpot');
    });

    test('should show CRM sync status', async () => {
      await prospectPage.goto();
      await prospectPage.selectProspect(0);
      await prospectPage.enrichProspect();
      await prospectPage.syncToCrm();

      // Verify status badge shows synced
      await prospectPage.verifyCrmSyncStatus('synced');
    });

    test('should handle CRM sync failure gracefully', async () => {
      await prospectPage.goto();
      await prospectPage.selectProspect(0);
      await prospectPage.enrichProspect();

      // Mock CRM sync failure
      await apiMock.mockError('/api/crm/sync', 503, 'CRM connection failed');

      await prospectPage.syncToCrmButton.click();

      // Should show error
      await prospectPage.expectError('CRM connection failed');
      await prospectPage.verifyCrmSyncStatus('error');
    });

    test('should update existing CRM record', async ({ authenticatedPage }) => {
      await prospectPage.goto();

      // Select a prospect that's already synced
      const syncedProspect = prospectPage.page.locator('[data-testid="prospect-item"][data-crm-synced="true"]').first();
      await syncedProspect.click();
      await prospectPage.waitForLoadingComplete();

      // Re-sync should update
      await prospectPage.syncToCrm();

      await prospectPage.expectNotification('CRM record updated');
    });
  });

  test.describe('Import Functionality', () => {
    test('should import prospects from CSV', async ({ authenticatedPage }) => {
      await prospectPage.goto();

      // Click import button
      await prospectPage.importButton.click();

      // Upload CSV file
      const fileInput = authenticatedPage.locator('[data-testid="import-file-input"]');
      await fileInput.setInputFiles('tests/fixtures/prospects.csv');

      // Confirm import
      const confirmButton = authenticatedPage.locator('[data-testid="confirm-import-btn"]');
      await confirmButton.click();

      // Wait for import
      await prospectPage.waitForLoadingComplete();
      await prospectPage.expectNotification('imported successfully');
    });

    test('should preview import data before confirming', async ({ authenticatedPage }) => {
      await prospectPage.goto();
      await prospectPage.importButton.click();

      const fileInput = authenticatedPage.locator('[data-testid="import-file-input"]');
      await fileInput.setInputFiles('tests/fixtures/prospects.csv');

      // Preview should appear
      const preview = authenticatedPage.locator('[data-testid="import-preview"]');
      await expect(preview).toBeVisible();

      // Should show column mapping
      const columnMapping = authenticatedPage.locator('[data-testid="column-mapping"]');
      await expect(columnMapping).toBeVisible();
    });

    test('should handle import errors gracefully', async ({ authenticatedPage }) => {
      await prospectPage.goto();
      await prospectPage.importButton.click();

      // Upload invalid file
      const fileInput = authenticatedPage.locator('[data-testid="import-file-input"]');
      await fileInput.setInputFiles('tests/fixtures/invalid.txt');

      // Should show error
      const importError = authenticatedPage.locator('[data-testid="import-error"]');
      await expect(importError).toBeVisible();
      await expect(importError).toContainText('Invalid file format');
    });
  });

  test.describe('Complete Workflow', () => {
    test('should complete full prospect enrichment → CRM sync flow', async ({ mockData }) => {
      // Step 1: Navigate to prospects
      await prospectPage.goto();

      // Step 2: Add new prospect
      await prospectPage.startAddProspect();

      const prospect = mockData.prospect();
      await prospectPage.fillProspectForm({
        firstName: prospect.firstName,
        lastName: prospect.lastName,
        email: prospect.email,
        company: prospect.company,
        title: prospect.title,
        phone: prospect.phone,
        linkedIn: prospect.linkedIn,
      });

      // Step 3: Save prospect
      await prospectPage.saveProspect();
      await prospectPage.expectNotification('Prospect created');

      // Step 4: Enrich prospect data
      await prospectPage.enrichProspect();

      // Step 5: Verify enrichment
      await prospectPage.verifyProspectEnriched();
      const enrichmentData = await prospectPage.getEnrichmentData();
      expect(enrichmentData.verified).toBe(true);
      expect(enrichmentData.companyInsights).toBeTruthy();

      // Step 6: Sync to CRM
      await prospectPage.syncToCrm();

      // Step 7: Verify sync status
      await prospectPage.verifyCrmSyncStatus('synced');
      await prospectPage.expectNotification('Synced to CRM');
    });

    test('should handle multiple prospects in workflow', async ({ mockData }) => {
      await prospectPage.goto();

      // Add and process first prospect
      await prospectPage.startAddProspect();
      const prospect1 = mockData.prospect({ firstName: 'Alice' });
      await prospectPage.fillProspectForm({
        firstName: prospect1.firstName,
        lastName: prospect1.lastName,
        email: prospect1.email,
        company: prospect1.company,
      });
      await prospectPage.saveProspect();
      await prospectPage.enrichProspect();
      await prospectPage.syncToCrm();

      // Add and process second prospect
      await prospectPage.goto();
      await prospectPage.startAddProspect();
      const prospect2 = mockData.prospect({ firstName: 'Bob' });
      await prospectPage.fillProspectForm({
        firstName: prospect2.firstName,
        lastName: prospect2.lastName,
        email: prospect2.email,
        company: prospect2.company,
      });
      await prospectPage.saveProspect();
      await prospectPage.enrichProspect();
      await prospectPage.syncToCrm();

      // Both should be synced
      await prospectPage.goto();
      const syncedCount = await prospectPage.page.locator('[data-testid="prospect-item"][data-crm-synced="true"]').count();
      expect(syncedCount).toBeGreaterThanOrEqual(2);
    });

    test('should handle event list import → enrich → sync workflow', async ({ authenticatedPage }) => {
      await prospectPage.goto();

      // Import event list
      await prospectPage.importButton.click();
      const fileInput = authenticatedPage.locator('[data-testid="import-file-input"]');
      await fileInput.setInputFiles('tests/fixtures/event-attendees.csv');

      const confirmButton = authenticatedPage.locator('[data-testid="confirm-import-btn"]');
      await confirmButton.click();
      await prospectPage.waitForLoadingComplete();

      // Select all imported prospects
      await prospectPage.selectAllProspects();

      // Bulk enrich
      await prospectPage.bulkEnrich();
      await prospectPage.waitForLoadingComplete();

      // Bulk sync to CRM
      await prospectPage.bulkSync();
      await prospectPage.waitForLoadingComplete();

      await prospectPage.expectNotification('Synced to CRM');
    });
  });
});
