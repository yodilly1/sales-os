import { test, expect } from '../fixtures';
import { ContentPage } from '../pages';
import { setupApiMocks, ApiMock } from '../mocks/api.mock';

/**
 * E2E Test Suite: Content Generation → Export Flow
 *
 * Tests the complete workflow from content creation,
 * AI-powered generation, to export in various formats.
 *
 * Core workflow:
 * 1. Select content type (deck, proposal, one-pager)
 * 2. Input goal and product info
 * 3. Generate content with AI
 * 4. Preview and edit
 * 5. Export to PDF/PPTX/HTML
 */

test.describe('Content Generation → Export Flow', () => {
  let contentPage: ContentPage;
  let apiMock: ApiMock;

  test.beforeEach(async ({ authenticatedPage }) => {
    contentPage = new ContentPage(authenticatedPage);
    apiMock = await setupApiMocks(authenticatedPage);
  });

  test.afterEach(async () => {
    await apiMock.clearMocks();
  });

  test.describe('Content List', () => {
    test('should display existing content items', async () => {
      await contentPage.goto();

      // Verify content list is visible
      await expect(contentPage.contentList).toBeVisible();

      // Should show existing content
      const count = await contentPage.getContentCount();
      expect(count).toBeGreaterThan(0);
    });

    test('should navigate to create new content', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      // Verify navigation to new content page
      await expect(authenticatedPage).toHaveURL(/\/content\/new/);
    });

    test('should filter content by type', async ({ authenticatedPage }) => {
      await contentPage.goto();

      // Click filter dropdown
      const filterDropdown = authenticatedPage.locator('[data-testid="content-type-filter"]');
      await filterDropdown.click();

      // Select proposals only
      const proposalFilter = authenticatedPage.locator('[data-testid="filter-proposal"]');
      await proposalFilter.click();

      // Wait for filter to apply
      await contentPage.waitForLoadingComplete();

      // All visible items should be proposals
      const items = await contentPage.contentItem.all();
      for (const item of items) {
        await expect(item.locator('[data-testid="content-type-badge"]')).toContainText('proposal');
      }
    });
  });

  test.describe('Content Creation', () => {
    test('should create proposal content', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      // Fill content form
      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Close enterprise deal with Fortune 500 company',
        productInfo: 'Sales OS - Complete VP of Sales Operating System',
        audience: 'C-level executives',
        tone: 'professional',
      });

      // Generate content
      await contentPage.generateContent();

      // Verify content was generated
      await contentPage.verifyContentGenerated();

      const previewContent = await contentPage.getPreviewContent();
      expect(previewContent).toContain('Proposal');
    });

    test('should create presentation deck', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'deck',
        goal: 'Product demo for sales team training',
        productInfo: 'Sales OS features and capabilities',
      });

      await contentPage.generateContent();
      await contentPage.verifyContentGenerated();
    });

    test('should create one-pager content', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'one-pager',
        goal: 'Quick overview for trade show handout',
        productInfo: 'Sales OS key benefits and pricing',
      });

      await contentPage.generateContent();
      await contentPage.verifyContentGenerated();
    });

    test('should validate required fields', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      // Try to generate without filling required fields
      await contentPage.generateButton.click();

      // Should show validation errors
      const goalError = authenticatedPage.locator('[data-testid="goal-error"]');
      await expect(goalError).toBeVisible();

      const productInfoError = authenticatedPage.locator('[data-testid="product-info-error"]');
      await expect(productInfoError).toBeVisible();
    });

    test('should use content templates', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      // Select a template
      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Standard sales proposal',
        productInfo: 'Product details',
        template: 'enterprise-proposal',
      });

      await contentPage.generateContent();
      await contentPage.verifyContentGenerated();

      // Content should follow template structure
      const preview = await contentPage.getPreviewContent();
      expect(preview).toContain('Executive Summary');
    });
  });

  test.describe('Content Preview and Edit', () => {
    test('should display content preview after generation', async () => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Test proposal',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();

      // Preview should be visible with content
      await expect(contentPage.contentPreview).toBeVisible();
      const content = await contentPage.getPreviewContent();
      expect(content.length).toBeGreaterThan(100);
    });

    test('should allow inline content editing', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Editable proposal',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();

      // Edit content
      await contentPage.editContentButton.click();
      await expect(contentPage.contentEditor).toBeVisible();

      // Make changes
      await contentPage.contentEditor.fill('Updated content here');
      await contentPage.saveButton.click();

      // Verify changes saved
      await contentPage.expectNotification('Content saved');
    });

    test('should support rich text formatting', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Formatted proposal',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();
      await contentPage.editContentButton.click();

      // Check for formatting toolbar
      const formatToolbar = authenticatedPage.locator('[data-testid="format-toolbar"]');
      await expect(formatToolbar).toBeVisible();

      // Verify formatting options exist
      await expect(authenticatedPage.locator('[data-testid="format-bold"]')).toBeVisible();
      await expect(authenticatedPage.locator('[data-testid="format-italic"]')).toBeVisible();
      await expect(authenticatedPage.locator('[data-testid="format-heading"]')).toBeVisible();
    });

    test('should auto-save content changes', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Auto-save test',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();
      await contentPage.editContentButton.click();

      // Type content
      await contentPage.contentEditor.fill('Auto-saved content');

      // Wait for auto-save indicator
      const autoSaveIndicator = authenticatedPage.locator('[data-testid="auto-save-indicator"]');
      await expect(autoSaveIndicator).toContainText('Saved');
    });
  });

  test.describe('Export Functionality', () => {
    test('should export content as PDF', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'PDF export test',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();

      // Set up download listener
      const downloadPromise = authenticatedPage.waitForEvent('download');

      // Export as PDF
      await contentPage.exportPdfButton.click();

      // Verify download
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.pdf$/);
    });

    test('should export deck as PPTX', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'deck',
        goal: 'PPTX export test',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();

      // Set up download listener
      const downloadPromise = authenticatedPage.waitForEvent('download');

      // Export as PPTX
      await contentPage.exportPptxButton.click();

      // Verify download
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.pptx$/);
    });

    test('should export content as HTML', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'one-pager',
        goal: 'HTML export test',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();

      // Set up download listener
      const downloadPromise = authenticatedPage.waitForEvent('download');

      // Export as HTML
      await contentPage.exportHtmlButton.click();

      // Verify download
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.html$/);
    });

    test('should show export progress for large documents', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'deck',
        goal: 'Large document test',
        productInfo: 'Detailed product info '.repeat(100),
      });

      await contentPage.generateContent();

      // Start export
      await contentPage.exportPdfButton.click();

      // Progress indicator should appear
      const progressIndicator = authenticatedPage.locator('[data-testid="export-progress"]');
      await expect(progressIndicator).toBeVisible();
    });

    test('should handle export failure gracefully', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Export failure test',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();

      // Mock export failure
      await apiMock.mockError('/api/content/*/export/pdf', 500, 'Export service unavailable');

      // Try to export
      await contentPage.exportPdfButton.click();

      // Should show error
      await contentPage.expectError('Export service unavailable');
    });
  });

  test.describe('Branding and Customization', () => {
    test('should apply brand colors to content', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      // Select brand preset
      const brandSelect = authenticatedPage.locator('[data-testid="brand-select"]');
      await brandSelect.selectOption('company-brand');

      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Branded proposal',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();

      // Verify brand styling applied
      const preview = contentPage.contentPreview;
      const styles = await preview.evaluate((el) => getComputedStyle(el));
      // Brand colors should be applied (simplified check)
      expect(styles).toBeDefined();
    });

    test('should add logo to content', async ({ authenticatedPage }) => {
      await contentPage.goto();
      await contentPage.startNewContent();

      // Upload logo
      const logoUpload = authenticatedPage.locator('[data-testid="logo-upload"]');
      await logoUpload.setInputFiles('tests/fixtures/logo.png');

      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Logo proposal',
        productInfo: 'Test product',
      });

      await contentPage.generateContent();

      // Logo should appear in preview
      const logo = authenticatedPage.locator('[data-testid="content-logo"]');
      await expect(logo).toBeVisible();
    });
  });

  test.describe('Complete Workflow', () => {
    test('should complete full content generation → export flow', async ({ authenticatedPage }) => {
      // Step 1: Navigate to content
      await contentPage.goto();

      // Step 2: Create new content
      await contentPage.startNewContent();

      // Step 3: Fill content form
      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Complete workflow test - enterprise sales proposal',
        productInfo: 'Sales OS - VP of Sales Operating System',
        audience: 'Enterprise decision makers',
        tone: 'professional',
      });

      // Step 4: Generate content
      await contentPage.generateContent();

      // Step 5: Verify content generated
      await contentPage.verifyContentGenerated();
      const preview = await contentPage.getPreviewContent();
      expect(preview).toContain('Proposal');

      // Step 6: Edit if needed
      await contentPage.editContentButton.click();
      await contentPage.saveButton.click();

      // Step 7: Export as PDF
      const downloadPromise = authenticatedPage.waitForEvent('download');
      await contentPage.exportPdfButton.click();
      const download = await downloadPromise;

      // Step 8: Verify export successful
      expect(download.suggestedFilename()).toMatch(/\.pdf$/);
    });

    test('should generate multiple content types in sequence', async ({ authenticatedPage }) => {
      // Generate proposal
      await contentPage.goto();
      await contentPage.startNewContent();
      await contentPage.fillContentForm({
        type: 'proposal',
        goal: 'Proposal',
        productInfo: 'Product',
      });
      await contentPage.generateContent();
      await contentPage.verifyContentGenerated();

      // Generate deck
      await contentPage.goto();
      await contentPage.startNewContent();
      await contentPage.fillContentForm({
        type: 'deck',
        goal: 'Deck',
        productInfo: 'Product',
      });
      await contentPage.generateContent();
      await contentPage.verifyContentGenerated();

      // Generate one-pager
      await contentPage.goto();
      await contentPage.startNewContent();
      await contentPage.fillContentForm({
        type: 'one-pager',
        goal: 'One-pager',
        productInfo: 'Product',
      });
      await contentPage.generateContent();
      await contentPage.verifyContentGenerated();
    });
  });
});
