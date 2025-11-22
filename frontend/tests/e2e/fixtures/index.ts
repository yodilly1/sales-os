import { test as base, expect, Page, BrowserContext } from '@playwright/test';

/**
 * Sales OS E2E Test Fixtures
 *
 * This module provides reusable fixtures and utilities for E2E testing.
 * Fixtures handle common setup/teardown patterns and provide typed helpers.
 */

// Types for test fixtures
export interface TestUser {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer';
  token?: string;
}

export interface TestFixtures {
  // Authenticated page with logged-in user
  authenticatedPage: Page;
  // Test user data
  testUser: TestUser;
  // API helper for making backend calls
  apiHelper: ApiHelper;
  // Mock data generator
  mockData: MockDataGenerator;
}

// API Helper for backend interactions during tests
export class ApiHelper {
  private baseUrl: string;
  private token?: string;

  constructor(baseUrl: string, token?: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async request(
    method: string,
    endpoint: string,
    data?: Record<string, unknown>
  ): Promise<Response> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });

    return response;
  }

  async get(endpoint: string): Promise<Response> {
    return this.request('GET', endpoint);
  }

  async post(endpoint: string, data: Record<string, unknown>): Promise<Response> {
    return this.request('POST', endpoint, data);
  }

  async put(endpoint: string, data: Record<string, unknown>): Promise<Response> {
    return this.request('PUT', endpoint, data);
  }

  async delete(endpoint: string): Promise<Response> {
    return this.request('DELETE', endpoint);
  }
}

// Mock Data Generator for creating test data
export class MockDataGenerator {
  private counter = 0;

  uniqueId(): string {
    return `test-${Date.now()}-${++this.counter}`;
  }

  email(): string {
    return `test-${this.uniqueId()}@example.com`;
  }

  // Generate mock transcript data
  transcript(overrides?: Partial<TranscriptMock>): TranscriptMock {
    return {
      id: this.uniqueId(),
      title: `Test Call - ${new Date().toISOString()}`,
      content: `
        Sales Rep: Hi, thanks for taking the time to chat today.
        Prospect: Of course, I've been looking for a solution like yours.
        Sales Rep: Great! Can you tell me about your current situation?
        Prospect: We're struggling with manual data entry and it's taking up 20 hours a week.
        Sales Rep: That sounds frustrating. What problems is this causing?
        Prospect: We're missing deadlines and our team morale is low.
        Sales Rep: I understand. What would it mean if you could solve this?
        Prospect: It would be huge - we could focus on actually growing the business.
      `,
      duration: 1800,
      participants: ['Sales Rep', 'Prospect'],
      createdAt: new Date().toISOString(),
      ...overrides,
    };
  }

  // Generate mock SPICED analysis
  spicedAnalysis(overrides?: Partial<SpicedAnalysisMock>): SpicedAnalysisMock {
    return {
      id: this.uniqueId(),
      transcriptId: this.uniqueId(),
      situation: 'Company struggling with manual data entry processes',
      problem: 'Spending 20+ hours per week on repetitive tasks',
      implication: 'Missing deadlines, low team morale, hindering growth',
      criticalEvent: 'End of quarter review coming up',
      decision: 'Need to make a decision within 30 days',
      createdAt: new Date().toISOString(),
      ...overrides,
    };
  }

  // Generate mock content data
  content(overrides?: Partial<ContentMock>): ContentMock {
    return {
      id: this.uniqueId(),
      type: 'proposal',
      title: 'Sales Proposal - Test Company',
      goal: 'Close deal with enterprise client',
      productInfo: 'Sales OS - VP of Sales Operating System',
      generatedContent: '<html><body><h1>Sales Proposal</h1></body></html>',
      format: 'pdf',
      createdAt: new Date().toISOString(),
      ...overrides,
    };
  }

  // Generate mock prospect data
  prospect(overrides?: Partial<ProspectMock>): ProspectMock {
    return {
      id: this.uniqueId(),
      firstName: 'John',
      lastName: 'Doe',
      email: this.email(),
      title: 'VP of Sales',
      company: 'Test Corp',
      phone: '+1-555-0123',
      linkedIn: 'https://linkedin.com/in/johndoe',
      verified: false,
      enrichmentData: null,
      createdAt: new Date().toISOString(),
      ...overrides,
    };
  }

  // Generate mock company data
  company(overrides?: Partial<CompanyMock>): CompanyMock {
    return {
      id: this.uniqueId(),
      name: 'Test Corporation',
      domain: 'testcorp.com',
      industry: 'Technology',
      size: '100-500',
      revenue: '$10M-$50M',
      location: 'San Francisco, CA',
      description: 'A leading technology company',
      createdAt: new Date().toISOString(),
      ...overrides,
    };
  }
}

// Mock data types
export interface TranscriptMock {
  id: string;
  title: string;
  content: string;
  duration: number;
  participants: string[];
  createdAt: string;
}

export interface SpicedAnalysisMock {
  id: string;
  transcriptId: string;
  situation: string;
  problem: string;
  implication: string;
  criticalEvent: string;
  decision: string;
  createdAt: string;
}

export interface ContentMock {
  id: string;
  type: 'proposal' | 'deck' | 'one-pager';
  title: string;
  goal: string;
  productInfo: string;
  generatedContent: string;
  format: 'pdf' | 'html' | 'pptx';
  createdAt: string;
}

export interface ProspectMock {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  title: string;
  company: string;
  phone: string;
  linkedIn: string;
  verified: boolean;
  enrichmentData: Record<string, unknown> | null;
  createdAt: string;
}

export interface CompanyMock {
  id: string;
  name: string;
  domain: string;
  industry: string;
  size: string;
  revenue: string;
  location: string;
  description: string;
  createdAt: string;
}

// Extended test with custom fixtures
export const test = base.extend<TestFixtures>({
  // Provide authenticated page
  authenticatedPage: async ({ page, context }, use) => {
    // Set up authentication state
    await context.addCookies([
      {
        name: 'auth_token',
        value: 'test-auth-token',
        domain: 'localhost',
        path: '/',
      },
    ]);

    // Set localStorage for auth state
    await page.addInitScript(() => {
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('user', JSON.stringify({
        id: 'test-user-1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'admin',
      }));
    });

    await use(page);
  },

  // Provide test user data
  testUser: async ({}, use) => {
    const user: TestUser = {
      id: 'test-user-1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'admin',
      token: 'test-auth-token',
    };
    await use(user);
  },

  // Provide API helper
  apiHelper: async ({ testUser }, use) => {
    const baseUrl = process.env.E2E_API_URL || 'http://localhost:8000';
    const helper = new ApiHelper(baseUrl, testUser.token);
    await use(helper);
  },

  // Provide mock data generator
  mockData: async ({}, use) => {
    const generator = new MockDataGenerator();
    await use(generator);
  },
});

export { expect };
