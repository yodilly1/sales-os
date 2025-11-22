'use client';

import { useRef, useState } from 'react';

interface AvatarUploadProps {
  currentAvatar?: string;
  name: string;
  onUpload: (file: File) => Promise<void>;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'w-16 h-16',
  md: 'w-24 h-24',
  lg: 'w-32 h-32',
};

export function AvatarUpload({
  currentAvatar,
  name,
  onUpload,
  size = 'md',
}: AvatarUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB');
      return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = (event) => {
      setPreviewUrl(event.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Upload
    setIsUploading(true);
    try {
      await onUpload(file);
    } catch {
      setPreviewUrl(null);
      alert('Failed to upload image. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const displayImage = previewUrl || currentAvatar;

  return (
    <div className="flex items-center gap-4">
      <div
        className={`${sizeClasses[size]} rounded-full overflow-hidden bg-gray-200 flex items-center justify-center relative`}
      >
        {displayImage ? (
          <img
            src={displayImage}
            alt={name}
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-xl font-medium text-gray-600">{initials}</span>
        )}
        {isUploading && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <svg
              className="w-6 h-6 text-white animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          </div>
        )}
      </div>

      <div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isUploading ? 'Uploading...' : 'Change photo'}
        </button>
        <p className="text-xs text-gray-500 mt-1">
          JPG, PNG or GIF. Max 5MB.
        </p>
      </div>
    </div>
  );
}

export default AvatarUpload;
