'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, FileText, Link, X, Check, AlertCircle } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Card, CardBody } from '@/components/common/Card';
import { cn } from '@/lib/utils';
import { TranscriptSource } from '@/lib/types';

interface TranscriptUploaderProps {
  onUpload: (data: UploadData) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

interface UploadData {
  type: 'file' | 'paste' | 'avoma';
  title: string;
  content?: string;
  file?: File;
  avomaId?: string;
  source: TranscriptSource;
}

type UploadMode = 'file' | 'paste' | 'avoma';

const uploadModes = [
  { id: 'file' as const, label: 'Upload File', icon: Upload, description: 'Upload .txt, .vtt, or .srt files' },
  { id: 'paste' as const, label: 'Paste Text', icon: FileText, description: 'Paste transcript text directly' },
  { id: 'avoma' as const, label: 'Avoma Sync', icon: Link, description: 'Import from Avoma' },
];

export function TranscriptUploader({ onUpload, isLoading = false, error }: TranscriptUploaderProps) {
  const [mode, setMode] = useState<UploadMode>('file');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [avomaId, setAvomaId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (isValidFile(droppedFile)) {
        setFile(droppedFile);
        if (!title) {
          setTitle(droppedFile.name.replace(/\.[^/.]+$/, ''));
        }
      }
    }
  }, [title]);

  const isValidFile = (file: File): boolean => {
    const validTypes = ['text/plain', 'text/vtt', 'text/srt', 'application/x-subrip'];
    const validExtensions = ['.txt', '.vtt', '.srt'];
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    return validTypes.includes(file.type) || validExtensions.includes(extension);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (isValidFile(selectedFile)) {
        setFile(selectedFile);
        if (!title) {
          setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
        }
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) return;

    const data: UploadData = {
      type: mode,
      title: title.trim(),
      source: mode === 'avoma' ? 'avoma' : 'manual',
    };

    if (mode === 'file' && file) {
      data.file = file;
    } else if (mode === 'paste' && content) {
      data.content = content;
    } else if (mode === 'avoma' && avomaId) {
      data.avomaId = avomaId;
    }

    await onUpload(data);
  };

  const isValid = () => {
    if (!title.trim()) return false;
    if (mode === 'file' && !file) return false;
    if (mode === 'paste' && !content.trim()) return false;
    if (mode === 'avoma' && !avomaId.trim()) return false;
    return true;
  };

  const resetForm = () => {
    setTitle('');
    setContent('');
    setAvomaId('');
    setFile(null);
  };

  return (
    <Card>
      <CardBody>
        {/* Mode Selector */}
        <div className="flex flex-wrap gap-2 mb-6">
          {uploadModes.map((uploadMode) => {
            const Icon = uploadMode.icon;
            const isActive = mode === uploadMode.id;
            return (
              <button
                key={uploadMode.id}
                onClick={() => {
                  setMode(uploadMode.id);
                  resetForm();
                }}
                className={cn(
                  'flex items-center gap-2 px-4 py-2.5 rounded-lg border transition-all',
                  isActive
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-neutral-200 bg-white text-neutral-600 hover:border-neutral-300'
                )}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium text-sm">{uploadMode.label}</span>
              </button>
            );
          })}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title Input */}
          <div>
            <label htmlFor="title" className="label">
              Transcript Title
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Discovery Call with Acme Corp"
              className="input"
              required
            />
          </div>

          {/* File Upload Mode */}
          {mode === 'file' && (
            <div>
              <label className="label">Upload File</label>
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={cn(
                  'relative border-2 border-dashed rounded-lg p-8 transition-colors text-center',
                  dragActive
                    ? 'border-primary-500 bg-primary-50'
                    : file
                    ? 'border-success-500 bg-success-50'
                    : 'border-neutral-300 hover:border-neutral-400'
                )}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.vtt,.srt"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />

                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <Check className="w-6 h-6 text-success-600" />
                    <div className="text-left">
                      <p className="font-medium text-neutral-900">{file.name}</p>
                      <p className="text-sm text-neutral-500">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setFile(null);
                      }}
                      className="p-1 rounded hover:bg-neutral-200"
                    >
                      <X className="w-4 h-4 text-neutral-500" />
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-neutral-400 mx-auto mb-2" />
                    <p className="text-neutral-600 font-medium">
                      Drag and drop your file here
                    </p>
                    <p className="text-sm text-neutral-500 mt-1">
                      or click to browse (.txt, .vtt, .srt)
                    </p>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Paste Text Mode */}
          {mode === 'paste' && (
            <div>
              <label htmlFor="content" className="label">
                Transcript Text
              </label>
              <textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste your transcript text here..."
                rows={12}
                className="input font-mono text-sm resize-none"
                required
              />
              <p className="helper-text">
                {content.length > 0
                  ? `${content.split(/\s+/).filter(Boolean).length} words`
                  : 'Paste the full transcript including speaker names and timestamps if available'}
              </p>
            </div>
          )}

          {/* Avoma Sync Mode */}
          {mode === 'avoma' && (
            <div>
              <label htmlFor="avomaId" className="label">
                Avoma Meeting ID or URL
              </label>
              <input
                id="avomaId"
                type="text"
                value={avomaId}
                onChange={(e) => setAvomaId(e.target.value)}
                placeholder="e.g., https://app.avoma.com/meetings/abc123 or abc123"
                className="input"
                required
              />
              <p className="helper-text">
                Enter the Avoma meeting ID or paste the full URL
              </p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-danger-50 text-danger-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={resetForm}
              disabled={isLoading}
            >
              Clear
            </Button>
            <Button
              type="submit"
              isLoading={isLoading}
              disabled={!isValid() || isLoading}
            >
              {mode === 'avoma' ? 'Sync from Avoma' : 'Upload & Analyze'}
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
