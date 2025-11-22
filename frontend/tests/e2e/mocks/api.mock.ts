import { Page, Route } from '@playwright/test';

/**
 * API Mock Handler for E2E Tests
 *
 * Provides mock responses for backend API calls during E2E testing.
 * This enables deterministic tests without depending on the backend.
 */

export interface MockConfig {
  delay?: number;
  status?: number;
  headers?: Record<string, string>;
}

export class ApiMock {
  private page: Page;
  private baseUrl: string;

  constructor(page: Page, baseUrl: string = 'http://localhost:8000') {
    this.page = page;
    this.baseUrl = baseUrl;
  }

  /**
   * Set up all API mocks
   */
  async setupAllMocks(): Promise<void> {
    await this.mockTranscriptEndpoints();
    await this.mockSpicedEndpoints();
    await this.mockContentEndpoints();
    await this.mockProspectEndpoints();
    await this.mockCrmEndpoints();
  }

  /**
   * Mock transcript-related endpoints
   */
  async mockTranscriptEndpoints(): Promise<void> {
    // GET /api/transcripts
    await this.page.route(`${this.baseUrl}/api/transcripts`, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            transcripts: [
              {
                id: 'transcript-1',
                title: 'Sales Call - Acme Corp',
                duration: 1800,
                createdAt: new Date().toISOString(),
                status: 'processed',
              },
              {
                id: 'transcript-2',
                title: 'Discovery Call - Tech Inc',
                duration: 2400,
                createdAt: new Date().toISOString(),
                status: 'pending',
              },
            ],
            total: 2,
          }),
        });
      }
    });

    // POST /api/transcripts
    await this.page.route(`${this.baseUrl}/api/transcripts`, async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: `transcript-${Date.now()}`,
            title: body?.title || 'New Transcript',
            content: body?.content,
            duration: body?.duration || 0,
            createdAt: new Date().toISOString(),
            status: 'processing',
          }),
        });
      }
    });

    // GET /api/transcripts/:id
    await this.page.route(`${this.baseUrl}/api/transcripts/*`, async (route) => {
      if (route.request().method() === 'GET') {
        const id = route.request().url().split('/').pop();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id,
            title: 'Sales Call - Acme Corp',
            content: `
              Sales Rep: Hi, thanks for taking the time to chat today.
              Prospect: Of course, I've been looking for a solution like yours.
              Sales Rep: Great! Can you tell me about your current situation?
              Prospect: We're struggling with manual data entry and it's taking up 20 hours a week.
              Sales Rep: That sounds frustrating. What problems is this causing?
              Prospect: We're missing deadlines and our team morale is low.
            `,
            duration: 1800,
            participants: ['Sales Rep', 'Prospect'],
            createdAt: new Date().toISOString(),
            status: 'processed',
          }),
        });
      }
    });
  }

  /**
   * Mock SPICED analysis endpoints
   */
  async mockSpicedEndpoints(): Promise<void> {
    // POST /api/spiced/analyze
    await this.page.route(`${this.baseUrl}/api/spiced/analyze`, async (route) => {
      // Simulate processing time
      await new Promise((resolve) => setTimeout(resolve, 500));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: `spiced-${Date.now()}`,
          transcriptId: route.request().postDataJSON()?.transcriptId,
          situation: 'Company struggling with manual data entry processes affecting productivity',
          problem: 'Spending 20+ hours per week on repetitive data entry tasks',
          implication: 'Missing deadlines, low team morale, unable to focus on growth initiatives',
          criticalEvent: 'End of quarter review approaching, need to show productivity improvements',
          decision: 'Need to make a decision within 30 days to impact Q4 results',
          confidence: 0.92,
          createdAt: new Date().toISOString(),
        }),
      });
    });

    // GET /api/spiced/:id
    await this.page.route(`${this.baseUrl}/api/spiced/*`, async (route) => {
      if (route.request().method() === 'GET') {
        const id = route.request().url().split('/').pop();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id,
            situation: 'Company struggling with manual data entry processes',
            problem: 'Spending 20+ hours per week on repetitive tasks',
            implication: 'Missing deadlines, low team morale',
            criticalEvent: 'End of quarter review',
            decision: 'Need decision within 30 days',
            confidence: 0.92,
          }),
        });
      }
    });
  }

  /**
   * Mock content generation endpoints
   */
  async mockContentEndpoints(): Promise<void> {
    // GET /api/content
    await this.page.route(`${this.baseUrl}/api/content`, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            content: [
              {
                id: 'content-1',
                type: 'proposal',
                title: 'Sales Proposal - Acme Corp',
                createdAt: new Date().toISOString(),
                status: 'completed',
              },
              {
                id: 'content-2',
                type: 'deck',
                title: 'Product Deck - Q4 2024',
                createdAt: new Date().toISOString(),
                status: 'draft',
              },
            ],
            total: 2,
          }),
        });
      }
    });

    // POST /api/content/generate
    await this.page.route(`${this.baseUrl}/api/content/generate`, async (route) => {
      // Simulate content generation time
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const body = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: `content-${Date.now()}`,
          type: body?.type || 'proposal',
          title: body?.title || 'Generated Content',
          goal: body?.goal,
          generatedContent: `
            <html>
              <head><title>${body?.title || 'Sales Document'}</title></head>
              <body>
                <h1>Sales Proposal</h1>
                <p>Goal: ${body?.goal}</p>
                <p>Product: ${body?.productInfo}</p>
                <section>
                  <h2>Executive Summary</h2>
                  <p>This proposal outlines how our solution can help address your needs...</p>
                </section>
                <section>
                  <h2>Solution Overview</h2>
                  <p>Our platform provides comprehensive tools for sales enablement...</p>
                </section>
              </body>
            </html>
          `,
          format: 'html',
          createdAt: new Date().toISOString(),
          status: 'completed',
        }),
      });
    });

    // GET /api/content/:id/export/:format
    await this.page.route(`${this.baseUrl}/api/content/*/export/*`, async (route) => {
      const url = route.request().url();
      const format = url.split('/').pop();

      await route.fulfill({
        status: 200,
        contentType: format === 'pdf' ? 'application/pdf' : 'application/octet-stream',
        body: Buffer.from('Mock file content'),
        headers: {
          'Content-Disposition': `attachment; filename="document.${format}"`,
        },
      });
    });
  }

  /**
   * Mock prospect endpoints
   */
  async mockProspectEndpoints(): Promise<void> {
    // GET /api/prospects
    await this.page.route(`${this.baseUrl}/api/prospects`, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            prospects: [
              {
                id: 'prospect-1',
                firstName: 'John',
                lastName: 'Doe',
                email: 'john.doe@acme.com',
                company: 'Acme Corp',
                title: 'VP of Sales',
                verified: true,
                crmSynced: true,
              },
              {
                id: 'prospect-2',
                firstName: 'Jane',
                lastName: 'Smith',
                email: 'jane.smith@techcorp.com',
                company: 'Tech Corp',
                title: 'Director of Operations',
                verified: false,
                crmSynced: false,
              },
            ],
            total: 2,
          }),
        });
      }
    });

    // POST /api/prospects
    await this.page.route(`${this.baseUrl}/api/prospects`, async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: `prospect-${Date.now()}`,
            ...body,
            verified: false,
            crmSynced: false,
            createdAt: new Date().toISOString(),
          }),
        });
      }
    });

    // POST /api/prospects/:id/enrich
    await this.page.route(`${this.baseUrl}/api/prospects/*/enrich`, async (route) => {
      // Simulate enrichment time
      await new Promise((resolve) => setTimeout(resolve, 800));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          verified: true,
          enrichmentData: {
            emailVerified: true,
            phoneVerified: true,
            linkedInProfile: 'https://linkedin.com/in/johndoe',
            companyInfo: {
              name: 'Acme Corp',
              industry: 'Technology',
              size: '100-500',
              revenue: '$10M-$50M',
              location: 'San Francisco, CA',
            },
            socialProfiles: {
              linkedin: 'https://linkedin.com/in/johndoe',
              twitter: 'https://twitter.com/johndoe',
            },
          },
          enrichedAt: new Date().toISOString(),
        }),
      });
    });
  }

  /**
   * Mock CRM endpoints
   */
  async mockCrmEndpoints(): Promise<void> {
    // POST /api/crm/sync
    await this.page.route(`${this.baseUrl}/api/crm/sync`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          syncedAt: new Date().toISOString(),
          crmId: `hubspot-${Date.now()}`,
          crmType: 'hubspot',
        }),
      });
    });

    // POST /api/crm/hubspot/sync
    await this.page.route(`${this.baseUrl}/api/crm/hubspot/sync`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          hubspotContactId: `hs-contact-${Date.now()}`,
          hubspotDealId: `hs-deal-${Date.now()}`,
          syncedAt: new Date().toISOString(),
        }),
      });
    });

    // GET /api/crm/status
    await this.page.route(`${this.baseUrl}/api/crm/status`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          connected: true,
          lastSync: new Date().toISOString(),
          provider: 'hubspot',
        }),
      });
    });
  }

  /**
   * Mock a specific endpoint with custom response
   */
  async mockEndpoint(
    path: string,
    response: unknown,
    options: MockConfig = {}
  ): Promise<void> {
    await this.page.route(`${this.baseUrl}${path}`, async (route) => {
      if (options.delay) {
        await new Promise((resolve) => setTimeout(resolve, options.delay));
      }

      await route.fulfill({
        status: options.status || 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
        headers: options.headers,
      });
    });
  }

  /**
   * Mock an endpoint to return an error
   */
  async mockError(
    path: string,
    status: number,
    message: string
  ): Promise<void> {
    await this.page.route(`${this.baseUrl}${path}`, async (route) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify({
          error: true,
          message,
          status,
        }),
      });
    });
  }

  /**
   * Clear all mocks
   */
  async clearMocks(): Promise<void> {
    await this.page.unrouteAll();
  }
}

/**
 * Create and set up API mocks for a page
 */
export async function setupApiMocks(page: Page): Promise<ApiMock> {
  const mock = new ApiMock(page, process.env.E2E_API_URL || 'http://localhost:8000');
  await mock.setupAllMocks();
  return mock;
}
