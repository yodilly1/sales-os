'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Plus,
  FileText,
  Clock,
  Users,
  Search,
  Filter,
  ArrowUpDown,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/common/Button';
import {
  Card,
  CardHeader,
  CardTitle,
  CardBody,
} from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { Modal } from '@/components/common/Modal';
import { TranscriptUploader } from '@/components/transcript/TranscriptUploader';
import { ProcessingStatusBadge } from '@/components/transcript/ProcessingStatus';
import { SPICEDScoreMini } from '@/components/spiced/SPICEDScores';
import { cn, formatDate, formatDuration } from '@/lib/utils';
import { transcriptApi } from '@/lib/api';
import {
  TranscriptListItem,
  TranscriptSource,
  ProcessingStatus,
  CRMStatus,
} from '@/lib/types';

const sourceLabels: Record<TranscriptSource, string> = {
  zoom: 'Zoom',
  teams: 'Teams',
  avoma: 'Avoma',
  manual: 'Manual',
};

const crmStatusConfig: Record<CRMStatus, { label: string; variant: 'success' | 'warning' | 'danger' | 'neutral' }> = {
  synced: { label: 'Synced', variant: 'success' },
  pending: { label: 'Pending', variant: 'warning' },
  failed: { label: 'Failed', variant: 'danger' },
  not_synced: { label: 'Not Synced', variant: 'neutral' },
};

export default function TranscriptsPage() {
  const [transcripts, setTranscripts] = useState<TranscriptListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | undefined>();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<'createdAt' | 'title'>('createdAt');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Load transcripts
  useEffect(() => {
    loadTranscripts();
  }, [sortField, sortDirection]);

  const loadTranscripts = async () => {
    try {
      setIsLoading(true);
      // Try to load from API, fall back to empty list
      try {
        const response = await transcriptApi.list({
          sort: { field: sortField, direction: sortDirection },
        });
        setTranscripts(response.data || []);
      } catch (apiError) {
        // API might not have a list endpoint yet, show empty state
        console.log('Transcript list API not available, showing empty state');
        setTranscripts([]);
      }
    } catch (error) {
      console.error('Failed to load transcripts:', error);
      setTranscripts([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (data: {
    type: string;
    title: string;
    content?: string;
    file?: File;
    avomaId?: string;
    source: TranscriptSource;
  }) => {
    setIsUploading(true);
    setUploadError(undefined);

    try {
      // Call real API based on upload type
      if (data.type === 'paste' && data.content) {
        // Use the parse endpoint for text content
        const response = await transcriptApi.parse({
          transcript_text: data.content,
          call_title: data.title,
          generate_tasks: true,
          generate_call_note: true,
        });

        // Add to list with data from response
        const newTranscript: TranscriptListItem = {
          id: response.transcript.id,
          title: response.transcript.title || data.title,
          source: data.source,
          duration: response.transcript.duration_minutes ? response.transcript.duration_minutes * 60 : 0,
          participantCount: response.transcript.speakers?.length || 0,
          status: 'completed',
          crmStatus: 'not_synced',
          createdAt: response.transcript.created_at,
        };
        setTranscripts((prev) => [newTranscript, ...prev]);
      } else if (data.type === 'file' && data.file) {
        // Use file upload endpoint
        const response = await transcriptApi.uploadFile(data.file, data.title);
        loadTranscripts(); // Refresh list
      } else if (data.type === 'avoma' && data.avomaId) {
        // Use Avoma sync endpoint
        const response = await transcriptApi.syncFromAvoma(data.avomaId, data.title);
        loadTranscripts(); // Refresh list
      }

      setShowUploadModal(false);
    } catch (error) {
      setUploadError(
        error instanceof Error ? error.message : 'Failed to upload transcript'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const filteredTranscripts = transcripts.filter((t) =>
    t.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleSort = (field: 'createdAt' | 'title') => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  if (isLoading) {
    return <PageLoading message="Loading transcripts..." />;
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Transcripts</h1>
          <p className="text-neutral-600 mt-1">
            Upload and analyze sales call transcripts with SPICED methodology
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/transcript/analyze">
            <Button variant="secondary">
              <FileText className="w-4 h-4 mr-2" />
              Analyze Transcript
            </Button>
          </Link>
          <Button
            onClick={() => setShowUploadModal(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Upload Transcript
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardBody className="py-3">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search transcripts..."
                className="input pl-10"
              />
            </div>

            {/* Sort */}
            <div className="flex gap-2">
              <Button
                variant={sortField === 'createdAt' ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => toggleSort('createdAt')}
                leftIcon={<ArrowUpDown className="w-4 h-4" />}
              >
                Date
              </Button>
              <Button
                variant={sortField === 'title' ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => toggleSort('title')}
                leftIcon={<ArrowUpDown className="w-4 h-4" />}
              >
                Name
              </Button>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Transcripts List */}
      {filteredTranscripts.length === 0 ? (
        <Card>
          <CardBody className="text-center py-12">
            <FileText className="w-12 h-12 text-neutral-300 mx-auto mb-4" />
            <h3 className="font-semibold text-neutral-900 mb-2">
              {searchQuery ? 'No matching transcripts' : 'No transcripts yet'}
            </h3>
            <p className="text-neutral-600 mb-4">
              {searchQuery
                ? 'Try adjusting your search query'
                : 'Upload your first transcript to get started with SPICED analysis'}
            </p>
            {!searchQuery && (
              <Button onClick={() => setShowUploadModal(true)}>
                Upload Transcript
              </Button>
            )}
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredTranscripts.map((transcript) => (
            <TranscriptCard key={transcript.id} transcript={transcript} />
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => {
          setShowUploadModal(false);
          setUploadError(undefined);
        }}
        title="Upload Transcript"
        description="Upload a call transcript for SPICED analysis"
        size="xl"
      >
        <TranscriptUploader
          onUpload={handleUpload}
          isLoading={isUploading}
          error={uploadError}
        />
      </Modal>
    </div>
  );
}

function TranscriptCard({ transcript }: { transcript: TranscriptListItem }) {
  const crmConfig = crmStatusConfig[transcript.crmStatus];

  return (
    <Link href={`/transcript/${transcript.id}`}>
      <Card className="group hover:shadow-elevated transition-shadow cursor-pointer">
        <CardBody className="py-4">
          <div className="flex items-center gap-4">
            {/* Icon */}
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
              <FileText className="w-5 h-5 text-primary-600" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold text-neutral-900 truncate group-hover:text-primary-600 transition-colors">
                  {transcript.title}
                </h3>
                <ProcessingStatusBadge status={transcript.status} />
              </div>
              <div className="flex items-center gap-4 text-sm text-neutral-500">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {formatDuration(transcript.duration)}
                </span>
                <span className="flex items-center gap-1">
                  <Users className="w-4 h-4" />
                  {transcript.participantCount} participants
                </span>
                <Badge variant="neutral" size="sm">
                  {sourceLabels[transcript.source]}
                </Badge>
              </div>
            </div>

            {/* Right side - Scores and Status */}
            <div className="flex items-center gap-4">
              {transcript.overallScore !== undefined && (
                <SPICEDScoreMini score={transcript.overallScore} />
              )}
              <Badge variant={crmConfig.variant} size="sm">
                CRM: {crmConfig.label}
              </Badge>
              <span className="text-sm text-neutral-500">
                {formatDate(transcript.createdAt)}
              </span>
              <ChevronRight className="w-5 h-5 text-neutral-400 group-hover:text-neutral-600 transition-colors" />
            </div>
          </div>
        </CardBody>
      </Card>
    </Link>
  );
}
