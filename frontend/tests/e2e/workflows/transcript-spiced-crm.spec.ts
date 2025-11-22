import { test, expect } from '../fixtures';
import { TranscriptPage } from '../pages';
import { setupApiMocks, ApiMock } from '../mocks/api.mock';

/**
 * E2E Test Suite: Transcript → SPICED → CRM Flow
 *
 * Tests the complete workflow from uploading a transcript,
 * analyzing it with SPICED methodology, and syncing to CRM.
 *
 * Core workflow:
 * 1. Upload or paste transcript
 * 2. Trigger SPICED analysis
 * 3. Review SPICED results
 * 4. Sync to CRM (HubSpot)
 */

test.describe('Transcript → SPICED → CRM Flow', () => {
  let transcriptPage: TranscriptPage;
  let apiMock: ApiMock;

  test.beforeEach(async ({ authenticatedPage }) => {
    transcriptPage = new TranscriptPage(authenticatedPage);
    apiMock = await setupApiMocks(authenticatedPage);
  });

  test.afterEach(async () => {
    await apiMock.clearMocks();
  });

  test.describe('Transcript Upload', () => {
    test('should display transcript list on page load', async () => {
      await transcriptPage.goto();

      // Verify transcript list is visible
      await expect(transcriptPage.transcriptList).toBeVisible();

      // Should show existing transcripts
      const count = await transcriptPage.getTranscriptCount();
      expect(count).toBeGreaterThan(0);
    });

    test('should paste transcript text and trigger analysis', async ({ mockData }) => {
      await transcriptPage.goto();

      // Create mock transcript content
      const transcript = mockData.transcript();

      // Paste transcript text
      await transcriptPage.pasteTranscriptText(transcript.content);

      // Verify text was entered
      await expect(transcriptPage.transcriptTextarea).toHaveValue(transcript.content);

      // Trigger analysis
      await transcriptPage.analyzeTranscript();

      // Verify SPICED results are displayed
      await transcriptPage.verifySpicedResultsDisplayed();
    });

    test('should handle empty transcript gracefully', async () => {
      await transcriptPage.goto();

      // Try to analyze without entering text
      await transcriptPage.pasteTranscriptText('');

      // Analyze button should be disabled or show error
      await expect(transcriptPage.analyzeButton).toBeDisabled();
    });
  });

  test.describe('SPICED Analysis', () => {
    test('should extract all SPICED components from transcript', async ({ mockData }) => {
      await transcriptPage.goto();

      // Paste transcript
      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);

      // Analyze
      await transcriptPage.analyzeTranscript();

      // Get SPICED results
      const results = await transcriptPage.getSpicedResults();

      // Verify all SPICED components are populated
      expect(results.situation).toBeTruthy();
      expect(results.problem).toBeTruthy();
      expect(results.implication).toBeTruthy();
      expect(results.criticalEvent).toBeTruthy();
      expect(results.decision).toBeTruthy();
    });

    test('should display SPICED results with confidence score', async ({ mockData, authenticatedPage }) => {
      await transcriptPage.goto();

      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);
      await transcriptPage.analyzeTranscript();

      // Verify confidence score is displayed
      const confidenceElement = authenticatedPage.locator('[data-testid="spiced-confidence"]');
      await expect(confidenceElement).toBeVisible();

      // Confidence should be a percentage
      const confidenceText = await confidenceElement.textContent();
      expect(confidenceText).toMatch(/\d+%/);
    });

    test('should allow editing SPICED results', async ({ mockData, authenticatedPage }) => {
      await transcriptPage.goto();

      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);
      await transcriptPage.analyzeTranscript();

      // Click edit button on situation field
      const editButton = authenticatedPage.locator('[data-testid="edit-situation-btn"]');
      await editButton.click();

      // Modify the situation text
      const situationInput = authenticatedPage.locator('[data-testid="situation-input"]');
      await situationInput.fill('Updated situation description');

      // Save changes
      const saveButton = authenticatedPage.locator('[data-testid="save-spiced-btn"]');
      await saveButton.click();

      // Verify update was saved
      await expect(transcriptPage.situationField).toContainText('Updated situation');
    });

    test('should handle analysis failure gracefully', async ({ authenticatedPage }) => {
      // Mock an error response
      await apiMock.mockError('/api/spiced/analyze', 500, 'Analysis service unavailable');

      await transcriptPage.goto();
      await transcriptPage.pasteTranscriptText('Some transcript content');

      // Try to analyze
      await transcriptPage.analyzeButton.click();

      // Should show error message
      await expect(transcriptPage.errorMessage).toBeVisible();
      await expect(transcriptPage.errorMessage).toContainText('unavailable');
    });
  });

  test.describe('CRM Sync', () => {
    test('should sync SPICED results to CRM', async ({ mockData }) => {
      await transcriptPage.goto();

      // Complete SPICED analysis first
      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);
      await transcriptPage.analyzeTranscript();

      // Sync to CRM
      await transcriptPage.syncToCrm();

      // Verify success notification
      await transcriptPage.expectNotification('Successfully synced to CRM');
    });

    test('should create CRM task from SPICED analysis', async ({ mockData, authenticatedPage }) => {
      await transcriptPage.goto();

      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);
      await transcriptPage.analyzeTranscript();

      // Create CRM task
      const createTaskButton = authenticatedPage.locator('[data-testid="create-crm-task-btn"]');
      await createTaskButton.click();

      // Fill task details
      const taskTitleInput = authenticatedPage.locator('[data-testid="task-title-input"]');
      await taskTitleInput.fill('Follow up on SPICED analysis');

      const taskDueDateInput = authenticatedPage.locator('[data-testid="task-due-date-input"]');
      await taskDueDateInput.fill('2024-12-31');

      // Submit task
      const submitTaskButton = authenticatedPage.locator('[data-testid="submit-task-btn"]');
      await submitTaskButton.click();

      // Verify task creation
      await transcriptPage.expectNotification('Task created successfully');
    });

    test('should create call note from transcript', async ({ mockData, authenticatedPage }) => {
      await transcriptPage.goto();

      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);
      await transcriptPage.analyzeTranscript();

      // Create call note
      const createNoteButton = authenticatedPage.locator('[data-testid="create-call-note-btn"]');
      await createNoteButton.click();

      // Note should be pre-populated with SPICED summary
      const noteTextarea = authenticatedPage.locator('[data-testid="call-note-textarea"]');
      const noteContent = await noteTextarea.inputValue();
      expect(noteContent).toContain('Situation');
      expect(noteContent).toContain('Problem');

      // Save note to CRM
      const saveNoteButton = authenticatedPage.locator('[data-testid="save-note-btn"]');
      await saveNoteButton.click();

      await transcriptPage.expectNotification('Note saved to CRM');
    });

    test('should handle CRM sync failure gracefully', async ({ mockData }) => {
      await transcriptPage.goto();

      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);
      await transcriptPage.analyzeTranscript();

      // Mock CRM sync failure
      await apiMock.mockError('/api/crm/sync', 503, 'CRM service unavailable');

      // Try to sync
      await transcriptPage.syncToCrmButton.click();

      // Should show error message
      await transcriptPage.expectError('CRM service unavailable');
    });

    test('should show CRM sync status indicator', async ({ mockData, authenticatedPage }) => {
      await transcriptPage.goto();

      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);
      await transcriptPage.analyzeTranscript();
      await transcriptPage.syncToCrm();

      // Verify sync status indicator
      const syncStatus = authenticatedPage.locator('[data-testid="crm-sync-status"]');
      await expect(syncStatus).toBeVisible();
      await expect(syncStatus).toHaveAttribute('data-status', 'synced');
    });
  });

  test.describe('Export Functionality', () => {
    test('should export SPICED results as PDF', async ({ mockData, authenticatedPage }) => {
      await transcriptPage.goto();

      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);
      await transcriptPage.analyzeTranscript();

      // Set up download listener
      const downloadPromise = authenticatedPage.waitForEvent('download');

      // Click export button
      await transcriptPage.exportButton.click();

      // Select PDF format
      const pdfOption = authenticatedPage.locator('[data-testid="export-pdf-option"]');
      await pdfOption.click();

      // Verify download started
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toContain('.pdf');
    });

    test('should export SPICED results as JSON', async ({ mockData, authenticatedPage }) => {
      await transcriptPage.goto();

      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);
      await transcriptPage.analyzeTranscript();

      // Set up download listener
      const downloadPromise = authenticatedPage.waitForEvent('download');

      // Click export button
      await transcriptPage.exportButton.click();

      // Select JSON format
      const jsonOption = authenticatedPage.locator('[data-testid="export-json-option"]');
      await jsonOption.click();

      // Verify download started
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toContain('.json');
    });
  });

  test.describe('Complete Workflow', () => {
    test('should complete full transcript → SPICED → CRM flow', async ({ mockData }) => {
      // Step 1: Navigate to transcripts
      await transcriptPage.goto();

      // Step 2: Create/paste transcript
      const transcript = mockData.transcript();
      await transcriptPage.pasteTranscriptText(transcript.content);

      // Step 3: Analyze transcript
      await transcriptPage.analyzeTranscript();

      // Step 4: Verify SPICED results
      await transcriptPage.verifySpicedResultsDisplayed();
      const results = await transcriptPage.getSpicedResults();
      expect(results.situation).toBeTruthy();
      expect(results.problem).toBeTruthy();

      // Step 5: Sync to CRM
      await transcriptPage.syncToCrm();

      // Step 6: Verify success
      await transcriptPage.expectNotification('Successfully synced');

      // Complete flow successful
    });

    test('should handle multiple transcripts in sequence', async ({ mockData }) => {
      await transcriptPage.goto();

      // Process first transcript
      const transcript1 = mockData.transcript({ title: 'Call 1' });
      await transcriptPage.pasteTranscriptText(transcript1.content);
      await transcriptPage.analyzeTranscript();
      await transcriptPage.syncToCrm();
      await transcriptPage.expectNotification('Successfully synced');

      // Navigate back and process second transcript
      await transcriptPage.goto();
      const transcript2 = mockData.transcript({ title: 'Call 2' });
      await transcriptPage.pasteTranscriptText(transcript2.content);
      await transcriptPage.analyzeTranscript();
      await transcriptPage.syncToCrm();
      await transcriptPage.expectNotification('Successfully synced');
    });
  });
});
