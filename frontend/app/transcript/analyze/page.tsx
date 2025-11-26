'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  FileText,
  Upload,
  Loader2,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Clock,
  Users,
  Target,
  TrendingUp,
  Calendar,
  UserCheck,
  ClipboardList,
  ArrowLeft,
} from 'lucide-react';
import { Button } from '@/components/common/Button';
import {
  Card,
  CardHeader,
  CardTitle,
  CardBody,
} from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { transcriptApi, TranscriptParseResponse } from '@/lib/api/transcript';
import Link from 'next/link';

interface SPICEDComponentProps {
  title: string;
  icon: React.ReactNode;
  summary: string;
  confidence: string;
  keyQuotes?: string[];
  details?: Record<string, string | string[] | null | undefined>;
}

function SPICEDComponent({ title, icon, summary, confidence, keyQuotes, details }: SPICEDComponentProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const confidenceColors: Record<string, string> = {
    high: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-orange-100 text-orange-800',
    not_found: 'bg-neutral-100 text-neutral-600',
  };

  return (
    <Card className="mb-4">
      <CardBody className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-neutral-900">{title}</h3>
              <Badge className={confidenceColors[confidence] || confidenceColors.medium} size="sm">
                {confidence}
              </Badge>
            </div>
            <p className="text-neutral-700">{summary}</p>

            {(keyQuotes?.length || details) && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 mt-2"
              >
                {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                {isExpanded ? 'Show less' : 'Show more'}
              </button>
            )}

            {isExpanded && (
              <div className="mt-3 space-y-3">
                {details && Object.entries(details).map(([key, value]) => {
                  if (!value || (Array.isArray(value) && value.length === 0)) return null;
                  return (
                    <div key={key}>
                      <span className="text-sm font-medium text-neutral-600 capitalize">
                        {key.replace(/_/g, ' ')}:
                      </span>
                      {Array.isArray(value) ? (
                        <ul className="ml-4 mt-1 list-disc list-inside text-sm text-neutral-700">
                          {value.map((item, i) => <li key={i}>{item}</li>)}
                        </ul>
                      ) : (
                        <span className="text-sm text-neutral-700 ml-1">{value}</span>
                      )}
                    </div>
                  );
                })}

                {keyQuotes && keyQuotes.length > 0 && (
                  <div>
                    <span className="text-sm font-medium text-neutral-600">Key Quotes:</span>
                    <div className="mt-1 space-y-2">
                      {keyQuotes.map((quote, i) => (
                        <blockquote key={i} className="border-l-2 border-primary-300 pl-3 text-sm italic text-neutral-600">
                          "{quote}"
                        </blockquote>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

export default function TranscriptAnalyzePage() {
  const router = useRouter();
  const [transcriptText, setTranscriptText] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [callTitle, setCallTitle] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TranscriptParseResponse | null>(null);

  const handleAnalyze = async () => {
    if (!transcriptText.trim() || transcriptText.length < 50) {
      setError('Please enter at least 50 characters of transcript text.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await transcriptApi.parse({
        transcript_text: transcriptText,
        company_name: companyName || undefined,
        call_title: callTitle || undefined,
        generate_tasks: true,
        generate_call_note: true,
      });
      setResult(response);
    } catch (err) {
      console.error('Analysis failed:', err);
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to analyze transcript. Please check your connection and try again.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setTranscriptText('');
    setCompanyName('');
    setCallTitle('');
    setResult(null);
    setError(null);
  };

  // If we have results, show them
  if (result) {
    const analysis = result.spiced_analysis;

    return (
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="sm" onClick={handleReset}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Analyze Another
          </Button>
        </div>

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">
              {result.transcript.title || 'SPICED Analysis Results'}
            </h1>
            <p className="text-neutral-600 mt-1">
              Analysis completed in {result.processing_time_ms}ms
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="success" size="lg">
              <CheckCircle className="w-4 h-4 mr-1" />
              Analysis Complete
            </Badge>
          </div>
        </div>

        {/* Warnings */}
        {result.warnings.length > 0 && (
          <Card className="mb-6 border-yellow-200 bg-yellow-50">
            <CardBody className="p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-yellow-800">Warnings</h4>
                  <ul className="mt-1 text-sm text-yellow-700">
                    {result.warnings.map((warning, i) => (
                      <li key={i}>{warning}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardBody>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* SPICED Analysis */}
          <div className="lg:col-span-2">
            <h2 className="text-lg font-semibold text-neutral-900 mb-4">SPICED Analysis</h2>

            <SPICEDComponent
              title="Situation"
              icon={<Target className="w-5 h-5 text-primary-600" />}
              summary={analysis.situation?.summary || 'No situation information found'}
              confidence={analysis.situation?.confidence || 'not_found'}
              keyQuotes={analysis.situation?.key_quotes}
              details={{
                current_tools: analysis.situation?.current_tools,
                team_size: analysis.situation?.team_size,
                industry_context: analysis.situation?.industry_context,
              }}
            />

            <SPICEDComponent
              title="Pain"
              icon={<AlertCircle className="w-5 h-5 text-primary-600" />}
              summary={analysis.pain?.primary_pain || 'No pain information found'}
              confidence={analysis.pain?.confidence || 'not_found'}
              keyQuotes={analysis.pain?.key_quotes}
              details={{
                secondary_pains: analysis.pain?.secondary_pains,
                symptoms: analysis.pain?.symptoms,
                root_causes: analysis.pain?.root_causes,
              }}
            />

            <SPICEDComponent
              title="Impact"
              icon={<TrendingUp className="w-5 h-5 text-primary-600" />}
              summary={analysis.impact?.business_impact || 'No impact information found'}
              confidence={analysis.impact?.confidence || 'not_found'}
              keyQuotes={analysis.impact?.key_quotes}
              details={{
                quantified_impact: analysis.impact?.quantified_impact,
                affected_areas: analysis.impact?.affected_areas,
                stakeholders_affected: analysis.impact?.stakeholders_affected,
                opportunity_cost: analysis.impact?.opportunity_cost,
              }}
            />

            <SPICEDComponent
              title="Critical Event"
              icon={<Calendar className="w-5 h-5 text-primary-600" />}
              summary={analysis.critical_event?.summary || 'No critical event information found'}
              confidence={analysis.critical_event?.confidence || 'not_found'}
              keyQuotes={analysis.critical_event?.key_quotes}
              details={{
                deadline: analysis.critical_event?.deadline,
                trigger_events: analysis.critical_event?.trigger_events,
                consequences_of_delay: analysis.critical_event?.consequences_of_delay,
                urgency_level: analysis.critical_event?.urgency_level,
              }}
            />

            <SPICEDComponent
              title="Expected Decision"
              icon={<UserCheck className="w-5 h-5 text-primary-600" />}
              summary={analysis.expected_decision?.summary || 'No decision information found'}
              confidence={analysis.expected_decision?.confidence || 'not_found'}
              keyQuotes={analysis.expected_decision?.key_quotes}
              details={{
                decision_maker: analysis.expected_decision?.decision_maker,
                stakeholders: analysis.expected_decision?.stakeholders,
                decision_timeline: analysis.expected_decision?.decision_timeline,
                approval_process: analysis.expected_decision?.approval_process,
                budget_authority: analysis.expected_decision?.budget_authority,
              }}
            />

            <SPICEDComponent
              title="Decision Criteria"
              icon={<ClipboardList className="w-5 h-5 text-primary-600" />}
              summary={analysis.decision_criteria?.summary || 'No decision criteria information found'}
              confidence={analysis.decision_criteria?.confidence || 'not_found'}
              keyQuotes={analysis.decision_criteria?.key_quotes}
              details={{
                must_haves: analysis.decision_criteria?.must_haves,
                nice_to_haves: analysis.decision_criteria?.nice_to_haves,
                deal_breakers: analysis.decision_criteria?.deal_breakers,
                competitors_considered: analysis.decision_criteria?.competitors_considered,
              }}
            />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Call Notes */}
            {result.call_note && (
              <Card>
                <CardHeader>
                  <CardTitle>Call Notes</CardTitle>
                </CardHeader>
                <CardBody>
                  <p className="text-sm text-neutral-700 mb-4">{result.call_note.summary}</p>
                  {result.call_note.customer_sentiment && (
                    <div className="mb-4">
                      <span className="text-xs font-medium text-neutral-500">Sentiment:</span>
                      <Badge variant="neutral" size="sm" className="ml-2">
                        {result.call_note.customer_sentiment}
                      </Badge>
                    </div>
                  )}
                  {result.call_note.key_discussion_points.length > 0 && (
                    <div>
                      <span className="text-xs font-medium text-neutral-500">Key Points:</span>
                      <ul className="mt-1 text-sm text-neutral-700 list-disc list-inside">
                        {result.call_note.key_discussion_points.map((point, i) => (
                          <li key={i}>{point}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardBody>
              </Card>
            )}

            {/* Follow-up Tasks */}
            {result.follow_up_tasks.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Follow-up Tasks</CardTitle>
                </CardHeader>
                <CardBody>
                  <div className="space-y-3">
                    {result.follow_up_tasks.map((task, i) => (
                      <div key={i} className="border-b border-neutral-100 pb-3 last:border-0 last:pb-0">
                        <div className="flex items-start gap-2">
                          <Badge
                            variant={task.priority === 'high' ? 'danger' : task.priority === 'medium' ? 'warning' : 'neutral'}
                            size="sm"
                          >
                            {task.priority}
                          </Badge>
                          <div className="flex-1">
                            <h4 className="text-sm font-medium text-neutral-900">{task.title}</h4>
                            <p className="text-xs text-neutral-500 mt-1">{task.description}</p>
                            {task.due_date_suggestion && (
                              <p className="text-xs text-neutral-400 mt-1">
                                Due: {task.due_date_suggestion}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardBody>
              </Card>
            )}

            {/* Gaps Identified */}
            {analysis.gaps_identified && analysis.gaps_identified.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Information Gaps</CardTitle>
                </CardHeader>
                <CardBody>
                  <ul className="space-y-2 text-sm text-neutral-700">
                    {analysis.gaps_identified.map((gap: string, i: number) => (
                      <li key={i} className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                        {gap}
                      </li>
                    ))}
                  </ul>
                </CardBody>
              </Card>
            )}

            {/* Coaching Notes */}
            {analysis.coaching_notes && analysis.coaching_notes.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Coaching Notes</CardTitle>
                </CardHeader>
                <CardBody>
                  <ul className="space-y-2 text-sm text-neutral-700">
                    {analysis.coaching_notes.map((note: string, i: number) => (
                      <li key={i} className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                        {note}
                      </li>
                    ))}
                  </ul>
                </CardBody>
              </Card>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Input form
  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <Link href="/" className="text-neutral-500 hover:text-neutral-700">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <h1 className="text-2xl font-bold text-neutral-900">Analyze Transcript</h1>
        </div>
        <p className="text-neutral-600">
          Paste your sales call transcript to extract SPICED methodology insights using AI
        </p>
      </div>

      <Card>
        <CardBody className="p-6">
          {/* Optional fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="callTitle" className="block text-sm font-medium text-neutral-700 mb-1">
                Call Title (optional)
              </label>
              <input
                id="callTitle"
                type="text"
                value={callTitle}
                onChange={(e) => setCallTitle(e.target.value)}
                placeholder="e.g., Discovery Call - Acme Corp"
                className="input"
              />
            </div>
            <div>
              <label htmlFor="companyName" className="block text-sm font-medium text-neutral-700 mb-1">
                Company Name (optional)
              </label>
              <input
                id="companyName"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g., Acme Corporation"
                className="input"
              />
            </div>
          </div>

          {/* Transcript input */}
          <div className="mb-4">
            <label htmlFor="transcript" className="block text-sm font-medium text-neutral-700 mb-1">
              Transcript Text
            </label>
            <textarea
              id="transcript"
              value={transcriptText}
              onChange={(e) => setTranscriptText(e.target.value)}
              placeholder="Paste your sales call transcript here...

Example format:
Sales Rep: Hi, thanks for meeting today. Tell me about your current billing challenges.
Prospect: We spend 20 hours a month on manual reconciliation. It's killing our team."
              className="input min-h-[300px] font-mono text-sm"
            />
            <p className="text-xs text-neutral-500 mt-1">
              Minimum 50 characters. Supports various formats: Zoom, Teams, Avoma, or plain text.
            </p>
          </div>

          {/* Error display */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-red-800">Error</h4>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Submit button */}
          <div className="flex justify-end">
            <Button
              onClick={handleAnalyze}
              disabled={isAnalyzing || transcriptText.length < 50}
              className="min-w-[150px]"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  Analyze Transcript
                </>
              )}
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Example transcripts */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">Example Transcript</h2>
        <Card>
          <CardBody className="p-4">
            <pre className="text-sm text-neutral-600 whitespace-pre-wrap font-mono">
{`Sales Rep: Hi, thanks for meeting today. Tell me about your current billing challenges.

Prospect: We spend 20 hours a month on manual reconciliation. It's killing our team.

Sales Rep: That sounds painful. What's the impact on your business?

Prospect: We're losing about $50,000 per quarter in billing errors, and our finance team is burned out.

Sales Rep: Is there a timeline you're working with to solve this?

Prospect: Our CFO wants something in place by Q2. We have a board meeting in March and need to show progress.

Sales Rep: Who else is involved in this decision?

Prospect: I'll be evaluating options with our VP of Finance, Sarah. The CFO will make the final call.`}
            </pre>
            <Button
              variant="ghost"
              size="sm"
              className="mt-3"
              onClick={() => setTranscriptText(`Sales Rep: Hi, thanks for meeting today. Tell me about your current billing challenges.

Prospect: We spend 20 hours a month on manual reconciliation. It's killing our team.

Sales Rep: That sounds painful. What's the impact on your business?

Prospect: We're losing about $50,000 per quarter in billing errors, and our finance team is burned out.

Sales Rep: Is there a timeline you're working with to solve this?

Prospect: Our CFO wants something in place by Q2. We have a board meeting in March and need to show progress.

Sales Rep: Who else is involved in this decision?

Prospect: I'll be evaluating options with our VP of Finance, Sarah. The CFO will make the final call.`)}
            >
              Use this example
            </Button>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
