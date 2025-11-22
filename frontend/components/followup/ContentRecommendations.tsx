'use client';

import React, { useState } from 'react';
import { FollowUpContentRecommendation, ContentRecommendation, ContentType } from './types';

interface ContentRecommendationsProps {
  recommendation: FollowUpContentRecommendation;
  onSelect?: (contentId: string) => void;
  onSend?: (contentId: string) => void;
  onDismiss?: () => void;
}

const contentTypeIcons: Record<ContentType, string> = {
  case_study: '📊',
  proposal: '📋',
  one_pager: '📄',
  battlecard: '⚔️',
  demo_video: '🎬',
  pricing_sheet: '💰',
  whitepaper: '📑',
  roi_calculator: '🧮',
};

const contentTypeLabels: Record<ContentType, string> = {
  case_study: 'Case Study',
  proposal: 'Proposal',
  one_pager: 'One-Pager',
  battlecard: 'Battlecard',
  demo_video: 'Demo Video',
  pricing_sheet: 'Pricing Sheet',
  whitepaper: 'Whitepaper',
  roi_calculator: 'ROI Calculator',
};

export function ContentRecommendations({
  recommendation,
  onSelect,
  onSend,
  onDismiss,
}: ContentRecommendationsProps) {
  const [selectedId, setSelectedId] = useState<string | null>(
    recommendation.selectedContentId || null
  );
  const [expandedId, setExpandedId] = useState<string | null>(null);

  function handleSelect(content: ContentRecommendation) {
    const id = content.contentId || content.contentType;
    setSelectedId(id);
    onSelect?.(id);
  }

  function handleSend() {
    if (selectedId) {
      onSend?.(selectedId);
    }
  }

  function getRelevanceColor(score: number): string {
    if (score >= 0.8) return '#22c55e';
    if (score >= 0.6) return '#3b82f6';
    if (score >= 0.4) return '#f59e0b';
    return '#94a3b8';
  }

  function getRelevanceLabel(score: number): string {
    if (score >= 0.8) return 'Highly Relevant';
    if (score >= 0.6) return 'Relevant';
    if (score >= 0.4) return 'Somewhat Relevant';
    return 'May Be Relevant';
  }

  const { recommendations, primaryRecommendation } = recommendation;

  return (
    <div className="content-recommendations">
      {/* Header */}
      <div className="header">
        <div className="title-section">
          <h3>Content Recommendations</h3>
          <span className="count">{recommendations.length} suggestions</span>
        </div>
        {onDismiss && (
          <button onClick={onDismiss} className="dismiss-btn">
            Dismiss
          </button>
        )}
      </div>

      {/* Primary recommendation */}
      {primaryRecommendation && (
        <div className="primary-recommendation">
          <div className="primary-label">Top Recommendation</div>
          <ContentCard
            content={primaryRecommendation}
            isSelected={selectedId === (primaryRecommendation.contentId || primaryRecommendation.contentType)}
            isExpanded={expandedId === (primaryRecommendation.contentId || primaryRecommendation.contentType)}
            onSelect={() => handleSelect(primaryRecommendation)}
            onToggleExpand={() => setExpandedId(
              expandedId === (primaryRecommendation.contentId || primaryRecommendation.contentType)
                ? null
                : (primaryRecommendation.contentId || primaryRecommendation.contentType)
            )}
            isPrimary
          />
        </div>
      )}

      {/* Other recommendations */}
      <div className="recommendations-list">
        {recommendations
          .filter((r) => r !== primaryRecommendation)
          .map((content) => {
            const id = content.contentId || content.contentType;
            return (
              <ContentCard
                key={id}
                content={content}
                isSelected={selectedId === id}
                isExpanded={expandedId === id}
                onSelect={() => handleSelect(content)}
                onToggleExpand={() => setExpandedId(expandedId === id ? null : id)}
              />
            );
          })}
      </div>

      {/* Actions */}
      {selectedId && onSend && (
        <div className="actions">
          <button onClick={handleSend} className="btn-send">
            Send Selected Content
          </button>
        </div>
      )}

      <style jsx>{`
        .content-recommendations {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          padding: 1.5rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .title-section {
          display: flex;
          align-items: baseline;
          gap: 0.75rem;
        }

        .title-section h3 {
          margin: 0;
          font-size: 1.125rem;
          font-weight: 600;
          color: #1e293b;
        }

        .count {
          font-size: 0.875rem;
          color: #64748b;
        }

        .dismiss-btn {
          padding: 0.375rem 0.75rem;
          font-size: 0.875rem;
          color: #64748b;
          background: transparent;
          border: 1px solid #e2e8f0;
          border-radius: 0.25rem;
          cursor: pointer;
        }

        .dismiss-btn:hover {
          background: #f1f5f9;
        }

        .primary-recommendation {
          position: relative;
        }

        .primary-label {
          position: absolute;
          top: -0.5rem;
          left: 1rem;
          padding: 0.125rem 0.5rem;
          font-size: 0.625rem;
          font-weight: 600;
          text-transform: uppercase;
          color: white;
          background: #8b5cf6;
          border-radius: 0.25rem;
          z-index: 1;
        }

        .recommendations-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .actions {
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .btn-send {
          padding: 0.75rem 1.5rem;
          font-weight: 500;
          color: white;
          background: #3b82f6;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-send:hover {
          background: #2563eb;
        }
      `}</style>
    </div>
  );
}

interface ContentCardProps {
  content: ContentRecommendation;
  isSelected: boolean;
  isExpanded: boolean;
  onSelect: () => void;
  onToggleExpand: () => void;
  isPrimary?: boolean;
}

function ContentCard({
  content,
  isSelected,
  isExpanded,
  onSelect,
  onToggleExpand,
  isPrimary = false,
}: ContentCardProps) {
  function getRelevanceColor(score: number): string {
    if (score >= 0.8) return '#22c55e';
    if (score >= 0.6) return '#3b82f6';
    if (score >= 0.4) return '#f59e0b';
    return '#94a3b8';
  }

  return (
    <div
      className={`content-card ${isSelected ? 'selected' : ''} ${isPrimary ? 'primary' : ''}`}
      onClick={onSelect}
    >
      <div className="card-main">
        <span className="type-icon">{contentTypeIcons[content.contentType]}</span>

        <div className="card-content">
          <div className="card-header">
            <h4 className="card-title">{content.title}</h4>
            <div className="badges">
              <span className="type-badge">
                {contentTypeLabels[content.contentType]}
              </span>
              <span
                className="relevance-badge"
                style={{ color: getRelevanceColor(content.relevanceScore) }}
              >
                {Math.round(content.relevanceScore * 100)}% relevant
              </span>
            </div>
          </div>

          <p className="card-description">{content.description}</p>

          {isExpanded && (
            <div className="expanded-content">
              <div className="reasoning">
                <strong>Why recommended:</strong>
                <p>{content.reasoning}</p>
              </div>

              {content.spicedElementsAddressed.length > 0 && (
                <div className="spiced-elements">
                  <strong>SPICED elements addressed:</strong>
                  <div className="element-tags">
                    {content.spicedElementsAddressed.map((element) => (
                      <span key={element} className="element-tag">
                        {element}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="card-actions">
          {isSelected && <span className="selected-check">✓</span>}
          <button
            className="expand-btn"
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand();
            }}
          >
            {isExpanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      <style jsx>{`
        .content-card {
          padding: 1rem;
          background: #f8fafc;
          border: 2px solid transparent;
          border-radius: 0.5rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .content-card:hover {
          background: #f1f5f9;
        }

        .content-card.selected {
          border-color: #3b82f6;
          background: #eff6ff;
        }

        .content-card.primary {
          border-color: #8b5cf6;
          background: #faf5ff;
        }

        .content-card.primary.selected {
          border-color: #3b82f6;
        }

        .card-main {
          display: flex;
          gap: 1rem;
          align-items: flex-start;
        }

        .type-icon {
          font-size: 1.5rem;
          flex-shrink: 0;
        }

        .card-content {
          flex: 1;
          min-width: 0;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
          margin-bottom: 0.5rem;
        }

        .card-title {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
          color: #1e293b;
        }

        .badges {
          display: flex;
          gap: 0.5rem;
          flex-shrink: 0;
        }

        .type-badge {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          color: #475569;
          background: white;
          border-radius: 0.25rem;
        }

        .relevance-badge {
          font-size: 0.75rem;
          font-weight: 500;
        }

        .card-description {
          margin: 0;
          font-size: 0.875rem;
          color: #64748b;
          line-height: 1.5;
        }

        .expanded-content {
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .reasoning,
        .spiced-elements {
          margin-bottom: 0.75rem;
        }

        .reasoning strong,
        .spiced-elements strong {
          font-size: 0.75rem;
          color: #64748b;
        }

        .reasoning p {
          margin: 0.25rem 0 0 0;
          font-size: 0.875rem;
          color: #1e293b;
        }

        .element-tags {
          display: flex;
          gap: 0.375rem;
          margin-top: 0.25rem;
          flex-wrap: wrap;
        }

        .element-tag {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          color: #7c3aed;
          background: #ede9fe;
          border-radius: 0.25rem;
          text-transform: capitalize;
        }

        .card-actions {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
        }

        .selected-check {
          width: 1.5rem;
          height: 1.5rem;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.875rem;
          color: white;
          background: #3b82f6;
          border-radius: 9999px;
        }

        .expand-btn {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          color: #64748b;
          background: transparent;
          border: none;
          cursor: pointer;
        }

        .expand-btn:hover {
          color: #1e293b;
        }
      `}</style>
    </div>
  );
}
