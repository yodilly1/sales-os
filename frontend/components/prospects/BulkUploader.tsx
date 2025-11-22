'use client'

import { useState, useRef, useCallback } from 'react'
import { Upload, FileText, X, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { cn, parseCSV } from '@/lib/utils'
import type { BulkUploadResponse } from '@/types'

interface BulkUploaderProps {
  onUpload: (file: File, name: string) => Promise<BulkUploadResponse>
  onUploadComplete?: (response: BulkUploadResponse) => void
  maxFileSizeMB?: number
  acceptedFormats?: string[]
}

interface PreviewData {
  headers: string[]
  rows: string[][]
  totalRows: number
}

export function BulkUploader({
  onUpload,
  onUploadComplete,
  maxFileSizeMB = 10,
  acceptedFormats = ['.csv'],
}: BulkUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const [batchName, setBatchName] = useState('')
  const [preview, setPreview] = useState<PreviewData | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadResult, setUploadResult] = useState<BulkUploadResponse | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = useCallback(
    (file: File): string | null => {
      const maxSize = maxFileSizeMB * 1024 * 1024
      if (file.size > maxSize) {
        return `File size exceeds ${maxFileSizeMB}MB limit`
      }

      const extension = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!acceptedFormats.includes(extension)) {
        return `Invalid file format. Accepted formats: ${acceptedFormats.join(', ')}`
      }

      return null
    },
    [maxFileSizeMB, acceptedFormats]
  )

  const processFile = useCallback(async (file: File) => {
    setError(null)
    setUploadResult(null)

    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }

    try {
      const content = await file.text()
      const { headers, rows } = parseCSV(content)

      setFile(file)
      setPreview({
        headers,
        rows: rows.slice(0, 5), // Show first 5 rows
        totalRows: rows.length,
      })
      setBatchName(file.name.replace(/\.[^/.]+$/, ''))
    } catch {
      setError('Failed to parse CSV file. Please ensure it is properly formatted.')
    }
  }, [validateFile])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)

      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile) {
        processFile(droppedFile)
      }
    },
    [processFile]
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0]
      if (selectedFile) {
        processFile(selectedFile)
      }
    },
    [processFile]
  )

  const handleUpload = async () => {
    if (!file || !batchName.trim()) return

    setIsUploading(true)
    setError(null)

    try {
      const response = await onUpload(file, batchName.trim())
      setUploadResult(response)
      onUploadComplete?.(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setPreview(null)
    setBatchName('')
    setError(null)
    setUploadResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Bulk Upload Prospects</h2>

      {!file && !uploadResult && (
        <>
          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
              isDragging
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={acceptedFormats.join(',')}
              onChange={handleFileSelect}
              className="hidden"
            />
            <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-600 mb-1">
              <span className="text-primary-600 font-medium">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500">
              CSV files up to {maxFileSizeMB}MB. Include columns for name, email, company, title.
            </p>
          </div>

          {/* Sample Format */}
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              Expected CSV Format
            </h4>
            <code className="text-xs text-gray-600 font-mono">
              name,email,company,title,linkedin_url
            </code>
          </div>
        </>
      )}

      {/* File Preview */}
      {file && preview && !uploadResult && (
        <div className="space-y-4">
          {/* File Info */}
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-primary-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">{file.name}</p>
                <p className="text-xs text-gray-500">
                  {preview.totalRows} records • {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            <button onClick={handleReset} className="p-1 hover:bg-gray-200 rounded">
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Batch Name Input */}
          <div>
            <label className="label">Batch Name</label>
            <input
              type="text"
              value={batchName}
              onChange={(e) => setBatchName(e.target.value)}
              placeholder="Enter a name for this batch"
              className="input"
            />
          </div>

          {/* Preview Table */}
          <div>
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              Preview (first 5 rows)
            </h4>
            <div className="overflow-x-auto border border-gray-200 rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {preview.headers.map((header, idx) => (
                      <th
                        key={idx}
                        className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {preview.rows.map((row, rowIdx) => (
                    <tr key={rowIdx}>
                      {row.map((cell, cellIdx) => (
                        <td
                          key={cellIdx}
                          className="px-3 py-2 text-sm text-gray-700 whitespace-nowrap max-w-[200px] truncate"
                        >
                          {cell || '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {preview.totalRows > 5 && (
              <p className="text-xs text-gray-500 mt-2 text-center">
                ... and {preview.totalRows - 5} more rows
              </p>
            )}
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={isUploading || !batchName.trim()}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload {preview.totalRows} Prospects
              </>
            )}
          </button>
        </div>
      )}

      {/* Upload Result */}
      {uploadResult && (
        <div className="space-y-4">
          <div
            className={cn(
              'p-4 rounded-lg flex items-start gap-3',
              uploadResult.success ? 'bg-success-50' : 'bg-error-50'
            )}
          >
            {uploadResult.success ? (
              <CheckCircle className="w-5 h-5 text-success-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0" />
            )}
            <div>
              <p
                className={cn(
                  'font-medium',
                  uploadResult.success ? 'text-success-800' : 'text-error-800'
                )}
              >
                {uploadResult.success ? 'Upload Successful!' : 'Upload Completed with Errors'}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {uploadResult.validRecords} of {uploadResult.totalRecords} records validated
                {uploadResult.invalidRecords > 0 && (
                  <span className="text-error-600">
                    {' '}
                    ({uploadResult.invalidRecords} invalid)
                  </span>
                )}
              </p>
            </div>
          </div>

          {/* Errors List */}
          {uploadResult.errors.length > 0 && (
            <div className="p-3 bg-error-50 rounded-lg">
              <h4 className="text-sm font-medium text-error-800 mb-2">Validation Errors:</h4>
              <ul className="text-sm text-error-700 space-y-1">
                {uploadResult.errors.slice(0, 5).map((err, idx) => (
                  <li key={idx}>• {err}</li>
                ))}
                {uploadResult.errors.length > 5 && (
                  <li className="text-error-600">
                    ... and {uploadResult.errors.length - 5} more errors
                  </li>
                )}
              </ul>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button onClick={handleReset} className="btn-secondary flex-1">
              Upload Another File
            </button>
            {uploadResult.success && (
              <button className="btn-primary flex-1">View Batch Progress</button>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-error-50 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0" />
          <p className="text-sm text-error-700">{error}</p>
        </div>
      )}
    </div>
  )
}

export default BulkUploader
