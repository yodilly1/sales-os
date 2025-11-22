'use client';

import React from 'react';
import { clsx } from 'clsx';
import type { SlideData } from './DeckViewer';

interface SlideProps {
  data: SlideData;
}

export function Slide({ data }: SlideProps) {
  const { content } = data;
  const layout = content.layout || 'title_content';

  const layoutClass = `layout-${layout.replace(/_/g, '-')}`;

  return (
    <div className={clsx('slide', layoutClass)}>
      {/* Title */}
      {content.title && <h1 className="slide-title">{content.title}</h1>}

      {/* Subtitle */}
      {content.subtitle && <p className="slide-subtitle">{content.subtitle}</p>}

      {/* Body Content */}
      {content.body && (
        <div className="slide-body">
          {content.body.map((block, i) => (
            <p key={i} className={block.style}>
              {block.content}
            </p>
          ))}
        </div>
      )}

      {/* Bullet Points */}
      {content.bullets && (
        <ul
          className={clsx(
            'slide-bullets',
            content.bullets.style === 'numbered' ? 'list-decimal' : 'list-disc'
          )}
        >
          {content.bullets.items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      )}

      {/* Image */}
      {content.image && (
        <div className="slide-image-container">
          <img
            src={content.image.url}
            alt={content.image.alt_text || ''}
            className="slide-image"
          />
        </div>
      )}

      {/* Metrics */}
      {content.metrics && (
        <div className="metrics-grid">
          {content.metrics.map((metric, i) => (
            <div key={i} className="metric-card">
              <div className="metric-value">{metric.value}</div>
              <div className="metric-label">{metric.label}</div>
              {metric.trend && (
                <div className={clsx('metric-trend', metric.trend)}>
                  {metric.trend === 'up' ? '↑' : metric.trend === 'down' ? '↓' : '→'}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Quote */}
      {content.quote && (
        <div className="quote-container">
          <blockquote className="quote-text">{content.quote}</blockquote>
          {content.quote_author && (
            <p className="quote-author">— {content.quote_author}</p>
          )}
        </div>
      )}

      {/* CTA Button */}
      {content.cta_text && (
        <div className="cta-container">
          <a
            href={content.cta_url || '#'}
            className="cta-button"
            target="_blank"
            rel="noopener noreferrer"
          >
            {content.cta_text}
          </a>
        </div>
      )}
    </div>
  );
}
