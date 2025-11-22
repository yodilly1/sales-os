'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Maximize,
  Minimize,
  Download,
  Monitor,
} from 'lucide-react';
import { clsx } from 'clsx';
import { Slide } from './Slide';

export interface SlideData {
  id: string;
  content: {
    layout?: string;
    title?: string;
    subtitle?: string;
    body?: Array<{ content: string; style?: string }>;
    bullets?: { items: string[]; style?: string };
    image?: { url: string; alt_text?: string };
    metrics?: Array<{ value: string; label: string; trend?: string }>;
    quote?: string;
    quote_author?: string;
    cta_text?: string;
    cta_url?: string;
    speaker_notes?: string;
  };
  transition?: string;
}

export interface DeckViewerConfig {
  enableNavigation?: boolean;
  enableFullscreen?: boolean;
  enablePresenterMode?: boolean;
  enableDownload?: boolean;
  autoAdvance?: boolean;
  autoAdvanceInterval?: number;
  theme?: 'light' | 'dark';
}

interface DeckViewerProps {
  slides: SlideData[];
  title?: string;
  config?: DeckViewerConfig;
  downloadUrl?: string;
  onSlideChange?: (index: number) => void;
}

export function DeckViewer({
  slides,
  title = 'Presentation',
  config = {},
  downloadUrl,
  onSlideChange,
}: DeckViewerProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const {
    enableNavigation = true,
    enableFullscreen = true,
    enablePresenterMode = true,
    enableDownload = true,
    autoAdvance = false,
    autoAdvanceInterval = 10,
    theme = 'dark',
  } = config;

  const totalSlides = slides.length;

  // Navigation functions
  const goToSlide = useCallback(
    (index: number) => {
      if (index >= 0 && index < totalSlides) {
        setCurrentSlide(index);
        onSlideChange?.(index);
      }
    },
    [totalSlides, onSlideChange]
  );

  const nextSlide = useCallback(() => {
    goToSlide(currentSlide + 1);
  }, [currentSlide, goToSlide]);

  const prevSlide = useCallback(() => {
    goToSlide(currentSlide - 1);
  }, [currentSlide, goToSlide]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowRight':
        case ' ':
        case 'PageDown':
          e.preventDefault();
          nextSlide();
          break;
        case 'ArrowLeft':
        case 'PageUp':
          e.preventDefault();
          prevSlide();
          break;
        case 'Home':
          e.preventDefault();
          goToSlide(0);
          break;
        case 'End':
          e.preventDefault();
          goToSlide(totalSlides - 1);
          break;
        case 'f':
        case 'F':
          e.preventDefault();
          toggleFullscreen();
          break;
        case 'Escape':
          if (isFullscreen) {
            toggleFullscreen();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentSlide, isFullscreen, nextSlide, prevSlide, goToSlide, totalSlides]);

  // Auto-advance
  useEffect(() => {
    if (!autoAdvance) return;

    const timer = setInterval(() => {
      if (currentSlide < totalSlides - 1) {
        nextSlide();
      }
    }, autoAdvanceInterval * 1000);

    return () => clearInterval(timer);
  }, [autoAdvance, autoAdvanceInterval, currentSlide, totalSlides, nextSlide]);

  // Touch navigation
  const [touchStart, setTouchStart] = useState<number | null>(null);

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.touches[0].clientX);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStart === null) return;

    const touchEnd = e.changedTouches[0].clientX;
    const diff = touchStart - touchEnd;

    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        nextSlide();
      } else {
        prevSlide();
      }
    }

    setTouchStart(null);
  };

  // Fullscreen
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () =>
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Presenter mode (opens new window)
  const openPresenterMode = () => {
    const presenterWindow = window.open(
      '',
      'presenter',
      'width=1200,height=800'
    );
    if (!presenterWindow) return;

    presenterWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Presenter View - ${title}</title>
        <style>
          body { margin: 0; background: #1a1a1a; color: white; font-family: system-ui; }
          .presenter-view { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; padding: 20px; height: 100vh; box-sizing: border-box; }
          .current-slide { background: white; border-radius: 8px; overflow: hidden; }
          .sidebar { display: flex; flex-direction: column; gap: 20px; }
          .next-slide { flex: 1; background: white; border-radius: 8px; opacity: 0.7; overflow: hidden; }
          .notes { background: #2d2d2d; padding: 20px; border-radius: 8px; overflow-y: auto; }
          .timer { background: #2d2d2d; padding: 20px; border-radius: 8px; text-align: center; font-size: 48px; font-family: monospace; }
        </style>
      </head>
      <body>
        <div class="presenter-view">
          <div class="current-slide">
            <p style="padding: 20px;">Current Slide: ${currentSlide + 1}</p>
          </div>
          <div class="sidebar">
            <div class="next-slide">
              <p style="padding: 20px; color: #333;">Next Slide: ${currentSlide + 2}</p>
            </div>
            <div class="notes">
              <h3>Speaker Notes</h3>
              <p>${slides[currentSlide]?.content.speaker_notes || 'No notes for this slide'}</p>
            </div>
            <div class="timer" id="timer">00:00:00</div>
          </div>
        </div>
        <script>
          let seconds = 0;
          setInterval(() => {
            seconds++;
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            document.getElementById('timer').textContent =
              String(h).padStart(2, '0') + ':' +
              String(m).padStart(2, '0') + ':' +
              String(s).padStart(2, '0');
          }, 1000);
        </script>
      </body>
      </html>
    `);
    presenterWindow.document.close();
  };

  const handleDownload = () => {
    if (downloadUrl) {
      window.location.href = downloadUrl;
    }
  };

  const progress = ((currentSlide + 1) / totalSlides) * 100;

  return (
    <div
      className={clsx(
        'deck-viewer',
        theme === 'dark' ? 'bg-gray-900' : 'bg-gray-100',
        isFullscreen && 'fullscreen'
      )}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Slide Container */}
      <div className="deck-container">
        <div className="slide-wrapper">
          {slides.map((slide, index) => (
            <div
              key={slide.id || index}
              style={{ display: index === currentSlide ? 'flex' : 'none' }}
            >
              <Slide data={slide} />
            </div>
          ))}
        </div>
      </div>

      {/* Controls */}
      <div className="deck-controls">
        {enableNavigation && (
          <>
            <button
              onClick={prevSlide}
              disabled={currentSlide === 0}
              title="Previous slide (←)"
            >
              <ChevronLeft size={20} />
            </button>

            <span className="slide-counter">
              {currentSlide + 1} / {totalSlides}
            </span>

            <button
              onClick={nextSlide}
              disabled={currentSlide === totalSlides - 1}
              title="Next slide (→)"
            >
              <ChevronRight size={20} />
            </button>
          </>
        )}

        {enableFullscreen && (
          <button onClick={toggleFullscreen} title="Fullscreen (F)">
            {isFullscreen ? <Minimize size={20} /> : <Maximize size={20} />}
          </button>
        )}

        {enablePresenterMode && (
          <button onClick={openPresenterMode} title="Presenter Mode">
            <Monitor size={20} />
          </button>
        )}

        {enableDownload && downloadUrl && (
          <button onClick={handleDownload} title="Download">
            <Download size={20} />
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div className="progress-bar">
        <div className="progress" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}
