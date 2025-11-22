import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Transcript Page Object
 *
 * Handles interactions with the transcript analysis page.
 * Used for Transcript → SPICED → CRM flow testing.
 */
export class TranscriptPage extends BasePage {
  // Page elements
  readonly uploadButton: Locator;
  readonly transcriptInput: Locator;
  readonly transcriptTextarea: Locator;
  readonly analyzeButton: Locator;
  readonly transcriptList: Locator;
  readonly transcriptItem: Locator;
  readonly spicedResults: Locator;
  readonly situationField: Locator;
  readonly problemField: Locator;
  readonly implicationField: Locator;
  readonly criticalEventField: Locator;
  readonly decisionField: Locator;
  readonly syncToCrmButton: Locator;
  readonly exportButton: Locator;

  constructor(page: Page) {
    super(page);

    // Upload and input elements
    this.uploadButton = page.locator('[data-testid="upload-transcript-btn"]');
    this.transcriptInput = page.locator('[data-testid="transcript-file-input"]');
    this.transcriptTextarea = page.locator('[data-testid="transcript-text-input"]');
    this.analyzeButton = page.locator('[data-testid="analyze-transcript-btn"]');

    // List elements
    this.transcriptList = page.locator('[data-testid="transcript-list"]');
    this.transcriptItem = page.locator('[data-testid="transcript-item"]');

    // SPICED analysis elements
    this.spicedResults = page.locator('[data-testid="spiced-results"]');
    this.situationField = page.locator('[data-testid="spiced-situation"]');
    this.problemField = page.locator('[data-testid="spiced-problem"]');
    this.implicationField = page.locator('[data-testid="spiced-implication"]');
    this.criticalEventField = page.locator('[data-testid="spiced-critical-event"]');
    this.decisionField = page.locator('[data-testid="spiced-decision"]');

    // Action buttons
    this.syncToCrmButton = page.locator('[data-testid="sync-to-crm-btn"]');
    this.exportButton = page.locator('[data-testid="export-spiced-btn"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('/transcripts');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to a specific transcript
   */
  async gotoTranscript(id: string): Promise<void> {
    await this.page.goto(`/transcripts/${id}`);
    await this.waitForPageLoad();
  }

  /**
   * Upload a transcript file
   */
  async uploadTranscript(filePath: string): Promise<void> {
    await this.uploadButton.click();
    await this.transcriptInput.setInputFiles(filePath);
    await this.waitForLoadingComplete();
  }

  /**
   * Paste transcript text directly
   */
  async pasteTranscriptText(text: string): Promise<void> {
    await this.transcriptTextarea.fill(text);
  }

  /**
   * Trigger SPICED analysis
   */
  async analyzeTranscript(): Promise<void> {
    await this.analyzeButton.click();
    await this.waitForLoadingComplete();
    // Wait for SPICED results to appear
    await this.spicedResults.waitFor({ state: 'visible', timeout: 30000 });
  }

  /**
   * Get SPICED analysis results
   */
  async getSpicedResults(): Promise<{
    situation: string;
    problem: string;
    implication: string;
    criticalEvent: string;
    decision: string;
  }> {
    return {
      situation: await this.getText(this.situationField),
      problem: await this.getText(this.problemField),
      implication: await this.getText(this.implicationField),
      criticalEvent: await this.getText(this.criticalEventField),
      decision: await this.getText(this.decisionField),
    };
  }

  /**
   * Sync SPICED results to CRM
   */
  async syncToCrm(): Promise<void> {
    await this.syncToCrmButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Export SPICED results
   */
  async exportResults(): Promise<void> {
    await this.exportButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Verify SPICED results are displayed
   */
  async verifySpicedResultsDisplayed(): Promise<void> {
    await expect(this.spicedResults).toBeVisible();
    await expect(this.situationField).not.toBeEmpty();
    await expect(this.problemField).not.toBeEmpty();
    await expect(this.implicationField).not.toBeEmpty();
  }

  /**
   * Get number of transcripts in list
   */
  async getTranscriptCount(): Promise<number> {
    return await this.transcriptItem.count();
  }

  /**
   * Click on a transcript in the list
   */
  async selectTranscript(index: number): Promise<void> {
    await this.transcriptItem.nth(index).click();
    await this.waitForLoadingComplete();
  }
}
