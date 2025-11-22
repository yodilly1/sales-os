import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Content Generator Page Object
 *
 * Handles interactions with the content generation page.
 * Used for Content generation → Export flow testing.
 */
export class ContentPage extends BasePage {
  // Page elements
  readonly createContentButton: Locator;
  readonly contentTypeSelect: Locator;
  readonly goalInput: Locator;
  readonly productInfoInput: Locator;
  readonly audienceInput: Locator;
  readonly toneSelect: Locator;
  readonly generateButton: Locator;
  readonly contentPreview: Locator;
  readonly contentList: Locator;
  readonly contentItem: Locator;
  readonly exportPdfButton: Locator;
  readonly exportPptxButton: Locator;
  readonly exportHtmlButton: Locator;
  readonly downloadButton: Locator;
  readonly editContentButton: Locator;
  readonly contentEditor: Locator;
  readonly saveButton: Locator;
  readonly templateSelect: Locator;

  constructor(page: Page) {
    super(page);

    // Creation elements
    this.createContentButton = page.locator('[data-testid="create-content-btn"]');
    this.contentTypeSelect = page.locator('[data-testid="content-type-select"]');
    this.goalInput = page.locator('[data-testid="content-goal-input"]');
    this.productInfoInput = page.locator('[data-testid="product-info-input"]');
    this.audienceInput = page.locator('[data-testid="audience-input"]');
    this.toneSelect = page.locator('[data-testid="tone-select"]');
    this.generateButton = page.locator('[data-testid="generate-content-btn"]');
    this.templateSelect = page.locator('[data-testid="template-select"]');

    // Preview and list elements
    this.contentPreview = page.locator('[data-testid="content-preview"]');
    this.contentList = page.locator('[data-testid="content-list"]');
    this.contentItem = page.locator('[data-testid="content-item"]');

    // Export elements
    this.exportPdfButton = page.locator('[data-testid="export-pdf-btn"]');
    this.exportPptxButton = page.locator('[data-testid="export-pptx-btn"]');
    this.exportHtmlButton = page.locator('[data-testid="export-html-btn"]');
    this.downloadButton = page.locator('[data-testid="download-btn"]');

    // Edit elements
    this.editContentButton = page.locator('[data-testid="edit-content-btn"]');
    this.contentEditor = page.locator('[data-testid="content-editor"]');
    this.saveButton = page.locator('[data-testid="save-content-btn"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('/content');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to a specific content item
   */
  async gotoContent(id: string): Promise<void> {
    await this.page.goto(`/content/${id}`);
    await this.waitForPageLoad();
  }

  /**
   * Start creating new content
   */
  async startNewContent(): Promise<void> {
    await this.createContentButton.click();
    await this.page.waitForURL(/\/content\/new/);
  }

  /**
   * Fill content generation form
   */
  async fillContentForm(options: {
    type: 'proposal' | 'deck' | 'one-pager';
    goal: string;
    productInfo: string;
    audience?: string;
    tone?: string;
    template?: string;
  }): Promise<void> {
    await this.contentTypeSelect.selectOption(options.type);
    await this.fillField(this.goalInput, options.goal);
    await this.fillField(this.productInfoInput, options.productInfo);

    if (options.audience) {
      await this.fillField(this.audienceInput, options.audience);
    }

    if (options.tone) {
      await this.toneSelect.selectOption(options.tone);
    }

    if (options.template) {
      await this.templateSelect.selectOption(options.template);
    }
  }

  /**
   * Generate content
   */
  async generateContent(): Promise<void> {
    await this.generateButton.click();
    await this.waitForLoadingComplete();
    // Wait for preview to appear (content generation can take time)
    await this.contentPreview.waitFor({ state: 'visible', timeout: 60000 });
  }

  /**
   * Export content as PDF
   */
  async exportAsPdf(): Promise<Download | void> {
    const downloadPromise = this.page.waitForEvent('download');
    await this.exportPdfButton.click();
    const download = await downloadPromise;
    return download;
  }

  /**
   * Export content as PPTX
   */
  async exportAsPptx(): Promise<Download | void> {
    const downloadPromise = this.page.waitForEvent('download');
    await this.exportPptxButton.click();
    const download = await downloadPromise;
    return download;
  }

  /**
   * Export content as HTML
   */
  async exportAsHtml(): Promise<Download | void> {
    const downloadPromise = this.page.waitForEvent('download');
    await this.exportHtmlButton.click();
    const download = await downloadPromise;
    return download;
  }

  /**
   * Edit content
   */
  async editContent(newContent: string): Promise<void> {
    await this.editContentButton.click();
    await this.contentEditor.waitFor({ state: 'visible' });
    await this.contentEditor.fill(newContent);
    await this.saveButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Get content preview text
   */
  async getPreviewContent(): Promise<string> {
    return await this.getText(this.contentPreview);
  }

  /**
   * Verify content was generated
   */
  async verifyContentGenerated(): Promise<void> {
    await expect(this.contentPreview).toBeVisible();
    await expect(this.contentPreview).not.toBeEmpty();
  }

  /**
   * Get number of content items in list
   */
  async getContentCount(): Promise<number> {
    return await this.contentItem.count();
  }

  /**
   * Select a content item from the list
   */
  async selectContent(index: number): Promise<void> {
    await this.contentItem.nth(index).click();
    await this.waitForLoadingComplete();
  }
}

// Type for download (simplified)
interface Download {
  suggestedFilename(): string;
  path(): Promise<string | null>;
  saveAs(path: string): Promise<void>;
}
