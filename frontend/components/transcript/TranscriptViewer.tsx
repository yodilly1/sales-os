'use client';

import { useState, useMemo } from 'react';
import { Search, User, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardBody } from '@/components/common/Card';
import { cn } from '@/lib/utils';
import { formatDuration } from '@/lib/utils';

interface TranscriptLine {
  id: string;
  speaker: string;
  timestamp?: number; // seconds from start
  text: string;
  isHighlighted?: boolean;
}

interface TranscriptViewerProps {
  rawText: string;
  duration?: number;
  participants?: { name: string; role: string }[];
  highlightedQuotes?: string[];
  className?: string;
}

export function TranscriptViewer({
  rawText,
  duration,
  participants = [],
  highlightedQuotes = [],
  className,
}: TranscriptViewerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isExpanded, setIsExpanded] = useState(true);
  const [showFullTranscript, setShowFullTranscript] = useState(false);

  // Parse raw text into structured lines
  const lines = useMemo(() => {
    const parsed: TranscriptLine[] = [];
    const linePattern = /^(?:\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*)?(?:([^:]+):\s*)?(.+)$/gm;

    let match;
    let index = 0;

    // Split by newlines and process each line
    const textLines = rawText.split('\n').filter(line => line.trim());

    for (const line of textLines) {
      const trimmedLine = line.trim();
      if (!trimmedLine) continue;

      // Try to parse speaker and timestamp
      const speakerMatch = trimmedLine.match(/^([^:]+):\s*(.+)$/);
      const timestampMatch = trimmedLine.match(/^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*/);

      let speaker = 'Unknown';
      let text = trimmedLine;
      let timestamp: number | undefined;

      if (timestampMatch) {
        const timeStr = timestampMatch[1];
        const parts = timeStr.split(':').map(Number);
        if (parts.length === 2) {
          timestamp = parts[0] * 60 + parts[1];
        } else if (parts.length === 3) {
          timestamp = parts[0] * 3600 + parts[1] * 60 + parts[2];
        }
        text = text.replace(timestampMatch[0], '');
      }

      if (speakerMatch) {
        speaker = speakerMatch[1].trim();
        text = speakerMatch[2].trim();
      }

      // Check if this line contains a highlighted quote
      const isHighlighted = highlightedQuotes.some(quote =>
        text.toLowerCase().includes(quote.toLowerCase())
      );

      parsed.push({
        id: `line-${index}`,
        speaker,
        timestamp,
        text,
        isHighlighted,
      });

      index++;
    }

    return parsed;
  }, [rawText, highlightedQuotes]);

  // Filter lines by search
  const filteredLines = useMemo(() => {
    if (!searchQuery) return lines;
    const query = searchQuery.toLowerCase();
    return lines.filter(
      (line) =>
        line.text.toLowerCase().includes(query) ||
        line.speaker.toLowerCase().includes(query)
    );
  }, [lines, searchQuery]);

  // Show limited lines unless expanded
  const displayedLines = showFullTranscript
    ? filteredLines
    : filteredLines.slice(0, 20);

  // Get unique speakers with colors
  const speakerColors = useMemo(() => {
    const colors = [
      'bg-primary-100 text-primary-700',
      'bg-accent-100 text-accent-700',
      'bg-success-100 text-success-700',
      'bg-warning-100 text-warning-700',
    ];
    const uniqueSpeakers = [...new Set(lines.map((l) => l.speaker))];
    return Object.fromEntries(
      uniqueSpeakers.map((speaker, i) => [speaker, colors[i % colors.length]])
    );
  }, [lines]);

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <CardTitle>Transcript</CardTitle>
          {duration && (
            <span className="flex items-center gap-1 text-sm text-neutral-500">
              <Clock className="w-4 h-4" />
              {formatDuration(duration)}
            </span>
          )}
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-2 rounded-lg hover:bg-neutral-100 text-neutral-500"
        >
          {isExpanded ? (
            <ChevronUp className="w-5 h-5" />
          ) : (
            <ChevronDown className="w-5 h-5" />
          )}
        </button>
      </CardHeader>

      {isExpanded && (
        <CardBody className="space-y-4">
          {/* Search and Participants */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search transcript..."
                className="input pl-10"
              />
            </div>
            {participants.length > 0 && (
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-neutral-400" />
                <span className="text-sm text-neutral-600">
                  {participants.length} participants
                </span>
              </div>
            )}
          </div>

          {/* Transcript Lines */}
          <div className="border border-neutral-200 rounded-lg overflow-hidden">
            <div className="max-h-[500px] overflow-y-auto">
              {displayedLines.length === 0 ? (
                <div className="p-8 text-center text-neutral-500">
                  {searchQuery
                    ? 'No matching lines found'
                    : 'No transcript content'}
                </div>
              ) : (
                <div className="divide-y divide-neutral-100">
                  {displayedLines.map((line) => (
                    <div
                      key={line.id}
                      className={cn(
                        'p-3 transition-colors hover:bg-neutral-50',
                        line.isHighlighted && 'bg-primary-50 hover:bg-primary-100'
                      )}
                    >
                      <div className="flex items-start gap-3">
                        {/* Timestamp */}
                        {line.timestamp !== undefined && (
                          <span className="flex-shrink-0 text-xs font-mono text-neutral-400 w-12">
                            {formatDuration(line.timestamp)}
                          </span>
                        )}

                        {/* Speaker Badge */}
                        <span
                          className={cn(
                            'flex-shrink-0 px-2 py-0.5 rounded text-xs font-medium',
                            speakerColors[line.speaker]
                          )}
                        >
                          {line.speaker}
                        </span>

                        {/* Text */}
                        <p className="text-sm text-neutral-700 flex-1">
                          {searchQuery ? (
                            <HighlightedText
                              text={line.text}
                              highlight={searchQuery}
                            />
                          ) : (
                            line.text
                          )}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Show More Button */}
          {filteredLines.length > 20 && (
            <button
              onClick={() => setShowFullTranscript(!showFullTranscript)}
              className="w-full py-2 text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              {showFullTranscript
                ? 'Show less'
                : `Show all ${filteredLines.length} lines`}
            </button>
          )}
        </CardBody>
      )}
    </Card>
  );
}

/**
 * Helper component to highlight search matches
 */
function HighlightedText({ text, highlight }: { text: string; highlight: string }) {
  if (!highlight) return <>{text}</>;

  const parts = text.split(new RegExp(`(${highlight})`, 'gi'));

  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === highlight.toLowerCase() ? (
          <mark key={i} className="bg-warning-200 text-warning-900 rounded px-0.5">
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </>
  );
}
