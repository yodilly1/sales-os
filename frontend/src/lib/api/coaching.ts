// Coaching API Client for Sales OS
// Handles all coaching-related API calls

import type {
  CoachingDashboardData,
  CoachingCall,
  CoachingMetrics,
  TrendDataPoint,
  TeamMember,
  WbDTip,
  CallFeedback,
} from '@/types/coaching';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, `API Error: ${response.statusText}`);
  }

  return response.json();
}

// Dashboard API
export async function getCoachingDashboard(): Promise<CoachingDashboardData> {
  return fetchApi<CoachingDashboardData>('/coaching/dashboard');
}

// Metrics API
export async function getCoachingMetrics(): Promise<CoachingMetrics> {
  return fetchApi<CoachingMetrics>('/coaching/metrics');
}

// Calls API
export async function getRecentCalls(limit = 10): Promise<CoachingCall[]> {
  return fetchApi<CoachingCall[]>(`/coaching/calls?limit=${limit}`);
}

export async function getCallById(callId: string): Promise<CoachingCall> {
  return fetchApi<CoachingCall>(`/coaching/calls/${callId}`);
}

export async function getCallFeedback(callId: string): Promise<CallFeedback[]> {
  return fetchApi<CallFeedback[]>(`/coaching/calls/${callId}/feedback`);
}

// Trends API
export async function getTrends(
  period: 'week' | 'month' | 'quarter' = 'month'
): Promise<TrendDataPoint[]> {
  return fetchApi<TrendDataPoint[]>(`/coaching/trends?period=${period}`);
}

// Team API
export async function getTeamLeaderboard(): Promise<TeamMember[]> {
  return fetchApi<TeamMember[]>('/coaching/team/leaderboard');
}

export async function getTeamMember(memberId: string): Promise<TeamMember> {
  return fetchApi<TeamMember>(`/coaching/team/${memberId}`);
}

// Tips API
export async function getWbDTips(
  element?: keyof Omit<import('@/types/coaching').SPICEDScores, 'overall'>
): Promise<WbDTip[]> {
  const query = element ? `?element=${element}` : '';
  return fetchApi<WbDTip[]>(`/coaching/tips${query}`);
}

// Mock data for development (remove in production)
export const mockDashboardData: CoachingDashboardData = {
  metrics: {
    totalCalls: 156,
    averageScore: 72,
    scoreChange: 8,
    topPerformer: 'Sarah Chen',
    improvementArea: 'criticalEvent',
    callsThisWeek: 23,
    callsChangePercent: 15,
  },
  recentCalls: [
    {
      id: '1',
      title: 'Discovery Call - Acme Corp',
      prospect: 'John Smith',
      company: 'Acme Corp',
      date: '2024-01-15T10:30:00Z',
      duration: 1800,
      scores: {
        situation: 85,
        pain: 78,
        impact: 72,
        criticalEvent: 65,
        decision: 80,
        overall: 76,
      },
      feedback: [],
      status: 'analyzed',
    },
    {
      id: '2',
      title: 'Demo Call - TechStart Inc',
      prospect: 'Emily Davis',
      company: 'TechStart Inc',
      date: '2024-01-14T14:00:00Z',
      duration: 2700,
      scores: {
        situation: 70,
        pain: 82,
        impact: 88,
        criticalEvent: 55,
        decision: 75,
        overall: 74,
      },
      feedback: [],
      status: 'analyzed',
    },
    {
      id: '3',
      title: 'Follow-up - Global Systems',
      prospect: 'Michael Brown',
      company: 'Global Systems',
      date: '2024-01-13T09:00:00Z',
      duration: 1200,
      scores: {
        situation: 90,
        pain: 85,
        impact: 80,
        criticalEvent: 70,
        decision: 88,
        overall: 83,
      },
      feedback: [],
      status: 'analyzed',
    },
  ],
  trends: [
    { date: '2024-01-08', situation: 70, pain: 65, impact: 68, criticalEvent: 55, decision: 72, overall: 66 },
    { date: '2024-01-09', situation: 72, pain: 68, impact: 70, criticalEvent: 58, decision: 74, overall: 68 },
    { date: '2024-01-10', situation: 75, pain: 70, impact: 72, criticalEvent: 60, decision: 76, overall: 71 },
    { date: '2024-01-11', situation: 73, pain: 72, impact: 75, criticalEvent: 62, decision: 78, overall: 72 },
    { date: '2024-01-12', situation: 78, pain: 75, impact: 78, criticalEvent: 65, decision: 80, overall: 75 },
    { date: '2024-01-13', situation: 80, pain: 78, impact: 80, criticalEvent: 68, decision: 82, overall: 78 },
    { date: '2024-01-14', situation: 82, pain: 80, impact: 82, criticalEvent: 70, decision: 84, overall: 80 },
  ],
  teamLeaderboard: [
    {
      id: '1',
      name: 'Sarah Chen',
      email: 'sarah@company.com',
      role: 'Senior AE',
      totalCalls: 45,
      averageScore: 85,
      trend: 'up',
      recentScores: { situation: 88, pain: 85, impact: 82, criticalEvent: 80, decision: 90, overall: 85 },
    },
    {
      id: '2',
      name: 'James Wilson',
      email: 'james@company.com',
      role: 'Account Executive',
      totalCalls: 38,
      averageScore: 78,
      trend: 'up',
      recentScores: { situation: 80, pain: 78, impact: 75, criticalEvent: 72, decision: 82, overall: 78 },
    },
    {
      id: '3',
      name: 'Maria Garcia',
      email: 'maria@company.com',
      role: 'SDR',
      totalCalls: 52,
      averageScore: 72,
      trend: 'stable',
      recentScores: { situation: 75, pain: 70, impact: 72, criticalEvent: 68, decision: 75, overall: 72 },
    },
    {
      id: '4',
      name: 'David Kim',
      email: 'david@company.com',
      role: 'Account Executive',
      totalCalls: 28,
      averageScore: 68,
      trend: 'down',
      recentScores: { situation: 70, pain: 65, impact: 68, criticalEvent: 60, decision: 70, overall: 68 },
    },
  ],
  tips: [
    {
      id: '1',
      element: 'criticalEvent',
      title: 'Identify the Critical Event',
      description: 'A critical event is the trigger that creates urgency. Without it, deals stall.',
      example: '"What happens if this problem isn\'t solved by Q2?"',
      actionItems: [
        'Ask about deadlines and consequences',
        'Understand the business impact of inaction',
        'Connect their timeline to your solution',
      ],
    },
    {
      id: '2',
      element: 'pain',
      title: 'Quantify the Pain',
      description: 'Help prospects understand the true cost of their current situation.',
      example: '"How much time does your team spend on this manual process each week?"',
      actionItems: [
        'Use open-ended questions to uncover pain',
        'Quantify pain in dollars, time, or risk',
        'Validate pain with multiple stakeholders',
      ],
    },
  ],
};

export const mockCallData: CoachingCall = {
  id: '1',
  title: 'Discovery Call - Acme Corp',
  prospect: 'John Smith',
  company: 'Acme Corp',
  date: '2024-01-15T10:30:00Z',
  duration: 1800,
  scores: {
    situation: 85,
    pain: 78,
    impact: 72,
    criticalEvent: 65,
    decision: 80,
    overall: 76,
  },
  feedback: [
    {
      id: 'f1',
      callId: '1',
      category: 'strength',
      spicedElement: 'situation',
      title: 'Strong Situation Discovery',
      content: 'Excellent job uncovering the current state of their operations. You asked detailed questions about their existing workflow and team structure.',
      createdAt: '2024-01-15T11:00:00Z',
    },
    {
      id: 'f2',
      callId: '1',
      category: 'improvement',
      spicedElement: 'criticalEvent',
      title: 'Missed Critical Event Opportunity',
      content: 'The prospect mentioned a board meeting in March but you didn\'t explore this further. This could have been a key critical event to anchor the timeline.',
      createdAt: '2024-01-15T11:00:00Z',
    },
    {
      id: 'f3',
      callId: '1',
      category: 'tip',
      spicedElement: 'impact',
      title: 'Quantify Business Impact',
      content: 'Try to connect the pain points to specific business metrics. Ask questions like "What would solving this mean for your quarterly targets?"',
      createdAt: '2024-01-15T11:00:00Z',
    },
  ],
  transcript: `Sales Rep: Hi John, thanks for taking the time today. I'd love to learn more about your current situation at Acme Corp.

John Smith: Sure, happy to chat. We've been struggling with our sales process efficiency lately.

Sales Rep: Tell me more about that. What does your current workflow look like?

John Smith: Well, we have about 20 sales reps, and they spend a lot of time on manual data entry and reporting...`,
  status: 'analyzed',
};
