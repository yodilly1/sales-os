// SPICED Coaching Types for Sales OS
// Based on Winning by Design methodology

export interface SPICEDScores {
  situation: number;
  pain: number;
  impact: number;
  criticalEvent: number;
  decision: number;
  overall: number;
}

export interface CallFeedback {
  id: string;
  callId: string;
  category: 'strength' | 'improvement' | 'tip';
  spicedElement?: keyof Omit<SPICEDScores, 'overall'>;
  title: string;
  content: string;
  timestamp?: string;
  createdAt: string;
}

export interface CoachingCall {
  id: string;
  title: string;
  prospect: string;
  company: string;
  date: string;
  duration: number; // in seconds
  scores: SPICEDScores;
  feedback: CallFeedback[];
  transcript?: string;
  recordingUrl?: string;
  status: 'analyzed' | 'pending' | 'failed';
}

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: string;
  totalCalls: number;
  averageScore: number;
  trend: 'up' | 'down' | 'stable';
  recentScores: SPICEDScores;
}

export interface TrendDataPoint {
  date: string;
  situation: number;
  pain: number;
  impact: number;
  criticalEvent: number;
  decision: number;
  overall: number;
}

export interface CoachingMetrics {
  totalCalls: number;
  averageScore: number;
  scoreChange: number;
  topPerformer: string;
  improvementArea: keyof Omit<SPICEDScores, 'overall'>;
  callsThisWeek: number;
  callsChangePercent: number;
}

export interface WbDTip {
  id: string;
  element: keyof Omit<SPICEDScores, 'overall'>;
  title: string;
  description: string;
  example?: string;
  actionItems: string[];
}

export interface CoachingDashboardData {
  metrics: CoachingMetrics;
  recentCalls: CoachingCall[];
  trends: TrendDataPoint[];
  teamLeaderboard: TeamMember[];
  tips: WbDTip[];
}
