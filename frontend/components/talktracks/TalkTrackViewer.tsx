'use client';

import { useState, useEffect } from 'react';
import { getTalkTrack, recordUsage } from '@/lib/api/talktracks';
import type { TalkTrack, ScriptSection, DiscoveryQuestion, ObjectionResponse } from '@/lib/api/talktracks';

interface TalkTrackViewerProps {
  talkTrackId: string;
}

const SPICED_COLORS: Record<string, string> = {
  situation: 'bg-blue-100 text-blue-800 border-blue-200',
  pain: 'bg-red-100 text-red-800 border-red-200',
  impact: 'bg-orange-100 text-orange-800 border-orange-200',
  critical_event: 'bg-purple-100 text-purple-800 border-purple-200',
  expected_decision: 'bg-green-100 text-green-800 border-green-200',
  decision_criteria: 'bg-teal-100 text-teal-800 border-teal-200',
};

export function TalkTrackViewer({ talkTrackId }: TalkTrackViewerProps) {
  const [talkTrack, setTalkTrack] = useState<TalkTrack | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'script' | 'questions' | 'objections' | 'tips'>('script');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['opening']));

  useEffect(() => {
    loadTalkTrack();
  }, [talkTrackId]);

  const loadTalkTrack = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getTalkTrack(talkTrackId);
      setTalkTrack(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load talk track');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSection = (sectionName: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sectionName)) {
        newSet.delete(sectionName);
      } else {
        newSet.add(sectionName);
      }
      return newSet;
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const handleRecordUsage = async () => {
    if (!talkTrack) return;
    try {
      await recordUsage({
        talktrack_id: talkTrack.id,
        user_id: 'current-user-id', // Would come from auth context
      });
      alert('Usage recorded!');
    } catch (err) {
      console.error('Failed to record usage:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
        Loading talk track...
      </div>
    );
  }

  if (error || !talkTrack) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center text-red-500">
        {error || 'Talk track not found'}
      </div>
    );
  }

  const renderSection = (section: ScriptSection, isOpen: boolean) => (
    <div key={section.name} className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => toggleSection(section.name)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-gray-400">{isOpen ? '▼' : '▶'}</span>
          <span className="font-medium text-gray-900">{section.name}</span>
          {section.duration_seconds && (
            <span className="text-xs text-gray-500">
              ~{Math.round(section.duration_seconds / 60)} min
            </span>
          )}
        </div>
        {section.spiced_elements && section.spiced_elements.length > 0 && (
          <div className="flex gap-1">
            {section.spiced_elements.map((element) => (
              <span
                key={element}
                className={`px-2 py-0.5 text-xs rounded ${SPICED_COLORS[element] || 'bg-gray-100 text-gray-800'}`}
              >
                {element.charAt(0).toUpperCase()}
              </span>
            ))}
          </div>
        )}
      </button>

      {isOpen && (
        <div className="p-4 space-y-4">
          {/* Script Content */}
          <div className="relative">
            <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded-lg font-sans">
              {section.content}
            </pre>
            <button
              onClick={() => copyToClipboard(section.content)}
              className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600"
              title="Copy to clipboard"
            >
              📋
            </button>
          </div>

          {/* Coaching Notes */}
          {section.coaching_notes && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-xs font-medium text-yellow-800 mb-1">Coaching Tip</p>
              <p className="text-sm text-yellow-700">{section.coaching_notes}</p>
            </div>
          )}

          {/* Transition Phrase */}
          {section.transition_phrase && (
            <div className="text-sm text-gray-500 italic">
              Transition: "{section.transition_phrase}"
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderDiscoveryQuestion = (question: DiscoveryQuestion, index: number) => (
    <div
      key={index}
      className={`p-4 rounded-lg border ${SPICED_COLORS[question.spiced_element] || 'border-gray-200 bg-white'}`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-medium uppercase tracking-wider">
          {question.spiced_element.replace('_', ' ')}
        </span>
      </div>

      <p className="font-medium text-gray-900 mb-2">"{question.question}"</p>

      {question.follow_up_questions && question.follow_up_questions.length > 0 && (
        <div className="mb-2">
          <p className="text-xs font-medium text-gray-500 mb-1">Follow-ups:</p>
          <ul className="text-sm text-gray-600 list-disc list-inside">
            {question.follow_up_questions.map((fq, i) => (
              <li key={i}>{fq}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-2 p-2 bg-white/50 rounded text-sm">
        <p className="text-xs font-medium text-gray-500 mb-1">Listen for:</p>
        <p className="text-gray-700">{question.what_to_listen_for}</p>
      </div>

      {question.coaching_tip && (
        <p className="mt-2 text-xs text-gray-500 italic">💡 {question.coaching_tip}</p>
      )}
    </div>
  );

  const renderObjectionResponse = (objection: ObjectionResponse, index: number) => (
    <div key={index} className="p-4 bg-white border border-gray-200 rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-orange-600 uppercase tracking-wider">
          {objection.category}
        </span>
      </div>

      <p className="font-medium text-gray-900 mb-3">"{objection.objection}"</p>

      <div className="space-y-3">
        <div className="p-2 bg-blue-50 rounded">
          <p className="text-xs font-medium text-blue-600 mb-1">Acknowledge:</p>
          <p className="text-sm text-blue-800">"{objection.acknowledge_phrase}"</p>
        </div>

        <div className="p-2 bg-green-50 rounded">
          <p className="text-xs font-medium text-green-600 mb-1">Response:</p>
          <p className="text-sm text-green-800">{objection.response}</p>
        </div>

        <div className="p-2 bg-purple-50 rounded">
          <p className="text-xs font-medium text-purple-600 mb-1">Reframe Strategy:</p>
          <p className="text-sm text-purple-800">{objection.reframe_strategy}</p>
        </div>

        {objection.proof_points && objection.proof_points.length > 0 && (
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-xs font-medium text-gray-600 mb-1">Proof Points:</p>
            <ul className="text-sm text-gray-700 list-disc list-inside">
              {objection.proof_points.map((pp, i) => (
                <li key={i}>{pp}</li>
              ))}
            </ul>
          </div>
        )}

        <p className="text-sm text-gray-500 italic">
          Transition: "{objection.transition_to_value}"
        </p>
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{talkTrack.title}</h2>
            {talkTrack.description && (
              <p className="mt-1 text-sm text-gray-500">{talkTrack.description}</p>
            )}
            <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
              <span>Persona: {talkTrack.persona.replace('_', ' ')}</span>
              <span>|</span>
              <span>Industry: {talkTrack.industry.replace('_', ' ')}</span>
              {talkTrack.total_duration_minutes && (
                <>
                  <span>|</span>
                  <span>Duration: ~{talkTrack.total_duration_minutes} min</span>
                </>
              )}
            </div>
          </div>
          <button
            onClick={handleRecordUsage}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
          >
            Use This Script
          </button>
        </div>

        {/* Tabs */}
        <div className="mt-4 flex gap-4 border-b border-gray-200 -mb-px">
          {[
            { id: 'script', label: 'Script' },
            { id: 'questions', label: 'Discovery Questions', show: !!talkTrack.discovery_questions?.length },
            { id: 'objections', label: 'Objection Responses', show: !!talkTrack.objection_responses?.length },
            { id: 'tips', label: 'Tips & Guidance' },
          ]
            .filter((tab) => tab.show !== false)
            .map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`
                  py-2 px-1 text-sm font-medium border-b-2 -mb-px
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'script' && (
          <div className="space-y-4">
            {renderSection(talkTrack.opening, expandedSections.has('opening'))}
            {talkTrack.sections.map((section) =>
              renderSection(section, expandedSections.has(section.name))
            )}
            {renderSection(talkTrack.closing, expandedSections.has('closing'))}
          </div>
        )}

        {activeTab === 'questions' && talkTrack.discovery_questions && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {talkTrack.discovery_questions.map((q, i) => renderDiscoveryQuestion(q, i))}
          </div>
        )}

        {activeTab === 'objections' && talkTrack.objection_responses && (
          <div className="space-y-4">
            {talkTrack.objection_responses.map((o, i) => renderObjectionResponse(o, i))}
          </div>
        )}

        {activeTab === 'tips' && (
          <div className="space-y-6">
            {talkTrack.key_tips && talkTrack.key_tips.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Key Tips</h3>
                <ul className="space-y-2">
                  {talkTrack.key_tips.map((tip, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <span className="text-green-500 mt-0.5">✓</span>
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {talkTrack.common_mistakes && talkTrack.common_mistakes.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Common Mistakes</h3>
                <ul className="space-y-2">
                  {talkTrack.common_mistakes.map((mistake, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <span className="text-red-500 mt-0.5">✗</span>
                      {mistake}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {talkTrack.success_metrics && talkTrack.success_metrics.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Success Metrics</h3>
                <ul className="space-y-2">
                  {talkTrack.success_metrics.map((metric, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <span className="text-blue-500 mt-0.5">★</span>
                      {metric}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
