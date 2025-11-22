'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Clock,
  Users,
  Calendar,
  ExternalLink,
  MoreHorizontal,
  Trash2,
  Download,
} from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Card, CardBody } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { Modal, ModalFooter } from '@/components/common/Modal';
import { ProcessingStatus } from '@/components/transcript/ProcessingStatus';
import { TranscriptViewer } from '@/components/transcript/TranscriptViewer';
import { TaskList } from '@/components/transcript/TaskList';
import { CallNotesEditor } from '@/components/transcript/CallNotesEditor';
import { CRMPushButton } from '@/components/transcript/CRMPushButton';
import { SPICEDScores } from '@/components/spiced/SPICEDScores';
import { SPICEDCard } from '@/components/spiced/SPICEDCard';
import { formatDate, formatDuration, cn } from '@/lib/utils';
import { transcriptApi } from '@/lib/api';
import {
  Transcript,
  SPICEDAnalysis,
  CallNotes,
  SuggestedTask,
  CRMPushRequest,
  CRMPushResponse,
  TranscriptSource,
} from '@/lib/types';

const sourceLabels: Record<TranscriptSource, string> = {
  zoom: 'Zoom',
  teams: 'Teams',
  avoma: 'Avoma',
  manual: 'Manual',
};

export default function TranscriptDetailPage() {
  const params = useParams();
  const router = useRouter();
  const transcriptId = params.id as string;

  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showActionsMenu, setShowActionsMenu] = useState(false);

  // Load transcript
  useEffect(() => {
    loadTranscript();
  }, [transcriptId]);

  const loadTranscript = async () => {
    try {
      setIsLoading(true);
      // In real implementation, this would call the API
      // For now, using mock data
      const mockTranscript: Transcript = {
        id: transcriptId,
        title: 'Discovery Call - Acme Corp',
        callId: 'call_123',
        rawText: `[0:00] Sarah (Rep): Hi John, thanks for taking the time to meet today. How are things going at Acme?

[0:15] John (Prospect): Thanks for having me. Things are busy as usual. We're really looking to streamline our sales process.

[0:30] Sarah (Rep): That's great to hear. What's driving that initiative?

[0:45] John (Prospect): Well, we've been struggling with visibility into our pipeline. Our reps are spending too much time on admin tasks instead of selling.

[1:15] Sarah (Rep): I hear that a lot. How much time would you estimate your team spends on administrative work?

[1:30] John (Prospect): Probably 40% of their day. It's really impacting our numbers. We missed our Q3 targets by 15%.

[2:00] Sarah (Rep): That's significant. What would it mean for the business if you could reclaim even half of that time?

[2:15] John (Prospect): We estimate it could add about $2M to our annual revenue. Our CEO is really pushing us to solve this before our board meeting in January.

[2:45] Sarah (Rep): January is coming up quickly. What does the decision process look like on your end?

[3:00] John (Prospect): I'm the main decision-maker, but I'll need buy-in from our VP of Finance and CTO. We're evaluating a couple of other solutions as well.

[3:30] Sarah (Rep): What criteria are most important as you evaluate solutions?

[3:45] John (Prospect): Integration with our existing CRM is critical. We also need something that's easy for our team to adopt. And of course, ROI - we need to see clear value.`,
        source: 'zoom',
        duration: 2580,
        participants: [
          { id: '1', name: 'Sarah', email: 'sarah@company.com', role: 'rep' },
          { id: '2', name: 'John', email: 'john@acme.com', role: 'prospect', company: 'Acme Corp' },
          { id: '3', name: 'Mike', email: 'mike@acme.com', role: 'participant', company: 'Acme Corp' },
        ],
        status: 'completed',
        spicedAnalysis: {
          id: 'analysis_1',
          transcriptId: transcriptId,
          elements: [
            {
              key: 'situation',
              label: 'Situation',
              content: 'Acme Corp is looking to streamline their sales process. They are a growing company with a sales team that is spending significant time on administrative tasks.',
              score: 4,
              quotes: ['We\'re really looking to streamline our sales process'],
              recommendations: ['Dig deeper into team size and current tools'],
            },
            {
              key: 'pain',
              label: 'Pain',
              content: 'Lack of visibility into pipeline and excessive time spent on admin tasks (40% of their day). This is directly impacting their sales performance.',
              score: 5,
              quotes: [
                'We\'ve been struggling with visibility into our pipeline',
                'Our reps are spending too much time on admin tasks',
                'Probably 40% of their day',
              ],
              recommendations: [],
            },
            {
              key: 'impact',
              label: 'Impact',
              content: 'Missed Q3 targets by 15%. Potential to add $2M to annual revenue if admin time is reduced.',
              score: 5,
              quotes: [
                'We missed our Q3 targets by 15%',
                'We estimate it could add about $2M to our annual revenue',
              ],
              recommendations: [],
            },
            {
              key: 'critical_event',
              label: 'Critical Event',
              content: 'Board meeting in January is driving urgency. CEO is pushing for a solution before then.',
              score: 4,
              quotes: ['Our CEO is really pushing us to solve this before our board meeting in January'],
              recommendations: ['Confirm exact date of board meeting', 'Understand what needs to be in place by then'],
            },
            {
              key: 'expected_decision',
              label: 'Expected Decision',
              content: 'John is the main decision-maker but needs buy-in from VP of Finance and CTO. They are evaluating multiple solutions.',
              score: 4,
              quotes: [
                'I\'m the main decision-maker',
                'I\'ll need buy-in from our VP of Finance and CTO',
                'We\'re evaluating a couple of other solutions',
              ],
              recommendations: ['Schedule meetings with VP Finance and CTO', 'Understand competitive landscape'],
            },
            {
              key: 'decision_criteria',
              label: 'Decision Criteria',
              content: 'CRM integration, ease of adoption, and clear ROI are the key criteria.',
              score: 4,
              quotes: [
                'Integration with our existing CRM is critical',
                'Something that\'s easy for our team to adopt',
                'We need to see clear value',
              ],
              recommendations: ['Prepare ROI analysis', 'Demo integration capabilities'],
            },
          ],
          overallScore: 4.3,
          summary: 'Excellent discovery call with strong qualification. Pain and Impact were well-uncovered with quantified business impact. Clear timeline with board meeting as critical event. Multi-threaded sale with defined decision criteria.',
          strengths: [
            'Quantified pain points effectively ($2M potential, 40% time on admin)',
            'Identified clear timeline and critical event (January board meeting)',
            'Good understanding of decision process and criteria',
          ],
          areasForImprovement: [
            'Could explore competitive landscape more',
            'Need to confirm exact board meeting date',
            'Should schedule calls with other stakeholders',
          ],
          coachingFeedback: 'Great job uncovering quantified pain and impact. For next call, focus on understanding the competitive evaluation process and getting introductions to the VP of Finance and CTO.',
          suggestedTasks: [
            {
              id: 'task_1',
              title: 'Send follow-up email with ROI analysis',
              description: 'Create and send a customized ROI analysis based on the $2M potential impact discussed',
              priority: 'high',
              dueDate: '2024-11-25',
              type: 'follow_up',
              completed: false,
            },
            {
              id: 'task_2',
              title: 'Schedule meeting with VP of Finance',
              description: 'Request introduction to VP of Finance to discuss budget and ROI requirements',
              priority: 'high',
              dueDate: '2024-11-27',
              type: 'follow_up',
              completed: false,
            },
            {
              id: 'task_3',
              title: 'Research competitive solutions',
              description: 'Research what other solutions Acme might be evaluating and prepare competitive positioning',
              priority: 'medium',
              dueDate: '2024-11-26',
              type: 'research',
              completed: false,
            },
            {
              id: 'task_4',
              title: 'Prepare integration demo',
              description: 'Prepare a demo showcasing CRM integration capabilities',
              priority: 'medium',
              dueDate: '2024-11-28',
              type: 'demo',
              completed: false,
            },
          ],
          createdAt: '2024-11-20T11:00:00Z',
          updatedAt: '2024-11-20T11:00:00Z',
        },
        callNotes: {
          id: 'notes_1',
          transcriptId: transcriptId,
          content: `## Key Takeaways

**Prospect:** John @ Acme Corp
**Meeting Type:** Discovery Call
**Date:** November 20, 2024

### Summary
Acme Corp is actively looking to streamline their sales process. Their team is spending 40% of their time on admin tasks, which caused them to miss Q3 targets by 15%. There's a potential $2M annual revenue impact if this is solved.

### Decision Timeline
- **Critical Event:** Board meeting in January
- **Decision Maker:** John (needs buy-in from VP Finance and CTO)
- **Competition:** Evaluating other solutions (need to research)

### Key Requirements
1. CRM integration (critical)
2. Easy team adoption
3. Clear ROI demonstration

### Next Steps
- [ ] Send ROI analysis
- [ ] Request intro to VP Finance
- [ ] Schedule integration demo
- [ ] Research competitive landscape`,
          autoGenerated: true,
          editedAt: undefined,
        },
        crmStatus: 'pending',
        createdAt: '2024-11-20T10:30:00Z',
        updatedAt: '2024-11-20T11:00:00Z',
      };

      setTranscript(mockTranscript);
    } catch (error) {
      console.error('Failed to load transcript:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleTask = async (taskId: string, completed: boolean) => {
    if (!transcript?.spicedAnalysis) return;

    // Update local state
    setTranscript((prev) => {
      if (!prev?.spicedAnalysis) return prev;
      return {
        ...prev,
        spicedAnalysis: {
          ...prev.spicedAnalysis,
          suggestedTasks: prev.spicedAnalysis.suggestedTasks.map((task) =>
            task.id === taskId ? { ...task, completed } : task
          ),
        },
      };
    });
  };

  const handleSaveNotes = async (content: string) => {
    // Update local state
    setTranscript((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        callNotes: {
          ...(prev.callNotes || { id: 'new', transcriptId: prev.id, autoGenerated: false }),
          content,
          editedAt: new Date().toISOString(),
        },
      };
    });
  };

  const handlePushToCRM = async (request: CRMPushRequest): Promise<CRMPushResponse> => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Update local state
    setTranscript((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        crmStatus: 'synced',
        crmRecordId: 'hubspot_123',
        crmPushedAt: new Date().toISOString(),
      };
    });

    return {
      success: true,
      recordId: 'hubspot_123',
      recordUrl: 'https://app.hubspot.com/contacts/123/deal/456',
    };
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      // In real implementation, call API
      await new Promise((resolve) => setTimeout(resolve, 1000));
      router.push('/transcript');
    } catch (error) {
      console.error('Failed to delete transcript:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return <PageLoading message="Loading transcript..." />;
  }

  if (!transcript) {
    return (
      <div className="max-w-7xl mx-auto text-center py-12">
        <h2 className="text-xl font-semibold text-neutral-900 mb-2">
          Transcript not found
        </h2>
        <p className="text-neutral-600 mb-4">
          The transcript you're looking for doesn't exist or has been deleted.
        </p>
        <Link href="/transcript">
          <Button variant="secondary">Back to Transcripts</Button>
        </Link>
      </div>
    );
  }

  const isProcessing = transcript.status === 'processing' || transcript.status === 'pending';

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        <div className="flex items-start gap-4">
          <Link
            href="/transcript"
            className="mt-1 p-2 rounded-lg hover:bg-neutral-100 text-neutral-500 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 mb-1">
              {transcript.title}
            </h1>
            <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-500">
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {formatDate(transcript.createdAt)}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatDuration(transcript.duration)}
              </span>
              <span className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                {transcript.participants.length} participants
              </span>
              <Badge variant="neutral">{sourceLabels[transcript.source]}</Badge>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <CRMPushButton
            transcriptId={transcript.id}
            crmStatus={transcript.crmStatus}
            crmRecordUrl={
              transcript.crmRecordId
                ? `https://app.hubspot.com/contacts/123/deal/${transcript.crmRecordId}`
                : undefined
            }
            onPush={handlePushToCRM}
          />

          <div className="relative">
            <Button
              variant="secondary"
              onClick={() => setShowActionsMenu(!showActionsMenu)}
            >
              <MoreHorizontal className="w-4 h-4" />
            </Button>

            {showActionsMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl border border-neutral-200 shadow-elevated z-50 animate-in">
                <div className="py-1">
                  <button className="flex items-center gap-2 w-full px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50">
                    <Download className="w-4 h-4" />
                    Export Transcript
                  </button>
                  <button className="flex items-center gap-2 w-full px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50">
                    <ExternalLink className="w-4 h-4" />
                    Open in Avoma
                  </button>
                  <hr className="my-1 border-neutral-100" />
                  <button
                    onClick={() => {
                      setShowActionsMenu(false);
                      setShowDeleteModal(true);
                    }}
                    className="flex items-center gap-2 w-full px-4 py-2 text-sm text-danger-600 hover:bg-neutral-50"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete Transcript
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Processing Status */}
      {isProcessing && (
        <ProcessingStatus
          status={transcript.status}
          progress={transcript.status === 'processing' ? 65 : 0}
          estimatedTime={transcript.status === 'processing' ? 45 : undefined}
          className="mb-6"
        />
      )}

      {/* Main Content Grid */}
      {!isProcessing && transcript.spicedAnalysis && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - SPICED Analysis */}
          <div className="lg:col-span-2 space-y-6">
            {/* Overall Scores */}
            <SPICEDScores analysis={transcript.spicedAnalysis} />

            {/* Individual SPICED Cards */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-neutral-900">
                Detailed Analysis
              </h2>
              {transcript.spicedAnalysis.elements.map((element) => (
                <SPICEDCard key={element.key} element={element} />
              ))}
            </div>

            {/* Transcript Viewer */}
            <TranscriptViewer
              rawText={transcript.rawText}
              duration={transcript.duration}
              participants={transcript.participants}
              highlightedQuotes={transcript.spicedAnalysis.elements.flatMap(
                (e) => e.quotes
              )}
            />
          </div>

          {/* Right Column - Notes and Tasks */}
          <div className="space-y-6">
            {/* Call Notes */}
            <CallNotesEditor
              notes={transcript.callNotes || null}
              onSave={handleSaveNotes}
            />

            {/* Tasks */}
            <TaskList
              tasks={transcript.spicedAnalysis.suggestedTasks}
              onToggleTask={handleToggleTask}
            />
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Transcript"
        size="sm"
      >
        <p className="text-neutral-600">
          Are you sure you want to delete this transcript? This action cannot be
          undone.
        </p>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleDelete}
            isLoading={isDeleting}
          >
            Delete
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
