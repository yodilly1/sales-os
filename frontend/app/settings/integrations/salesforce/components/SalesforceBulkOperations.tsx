"use client";

import { useState, useEffect, useRef } from "react";
import type { BulkJob, BulkJobResult } from "../types";

/**
 * Salesforce bulk operations monitoring and management component.
 */
export function SalesforceBulkOperations() {
  const [jobs, setJobs] = useState<BulkJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<BulkJobResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadConfig, setUploadConfig] = useState({
    sobjectType: "Lead",
    operation: "insert",
  });
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadJobs();
    // Poll for job updates every 10 seconds
    const interval = setInterval(loadJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadJobs = async () => {
    try {
      // Note: This endpoint would need to be implemented
      // For now, we'll use an empty array as placeholder
      setJobs([]);
    } catch (error) {
      console.error("Failed to load jobs:", error);
    }
  };

  const loadJobDetails = async (jobId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/salesforce/bulk/jobs/${jobId}`);
      const data = await response.json();
      setSelectedJob(data);
    } catch (error) {
      console.error("Failed to load job details:", error);
    } finally {
      setLoading(false);
    }
  };

  const abortJob = async (jobId: string) => {
    if (!confirm("Are you sure you want to abort this job?")) {
      return;
    }

    try {
      await fetch(`/api/salesforce/bulk/jobs/${jobId}/abort`, {
        method: "POST",
      });
      loadJobs();
    } catch (error) {
      console.error("Failed to abort job:", error);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;

    try {
      setUploading(true);

      // Parse CSV file
      const text = await uploadFile.text();
      const records = parseCSV(text);

      if (records.length === 0) {
        alert("No records found in file");
        return;
      }

      // Create bulk job
      const response = await fetch("/api/salesforce/bulk/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sobject_type: uploadConfig.sobjectType,
          operation: uploadConfig.operation,
          records,
        }),
      });

      if (response.ok) {
        alert(`Bulk job created with ${records.length} records`);
        setUploadFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
        loadJobs();
      } else {
        const error = await response.json();
        alert(`Failed to create job: ${error.detail}`);
      }
    } catch (error) {
      console.error("Failed to upload file:", error);
      alert("Failed to process file");
    } finally {
      setUploading(false);
    }
  };

  const parseCSV = (text: string): Record<string, unknown>[] => {
    const lines = text.split("\n").filter((line) => line.trim());
    if (lines.length < 2) return [];

    const headers = lines[0].split(",").map((h) => h.trim().replace(/"/g, ""));
    const records: Record<string, unknown>[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(",").map((v) => v.trim().replace(/"/g, ""));
      const record: Record<string, unknown> = {};

      headers.forEach((header, index) => {
        if (values[index]) {
          record[header] = values[index];
        }
      });

      if (Object.keys(record).length > 0) {
        records.push(record);
      }
    }

    return records;
  };

  const getStatusColor = (state: string) => {
    switch (state) {
      case "JobComplete":
        return "bg-green-100 text-green-700";
      case "InProgress":
      case "UploadComplete":
        return "bg-blue-100 text-blue-700";
      case "Aborted":
        return "bg-yellow-100 text-yellow-700";
      case "Failed":
        return "bg-red-100 text-red-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Bulk Data Upload
        </h3>

        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Salesforce Object
            </label>
            <select
              value={uploadConfig.sobjectType}
              onChange={(e) =>
                setUploadConfig((prev) => ({
                  ...prev,
                  sobjectType: e.target.value,
                }))
              }
              className="
                w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              "
            >
              <option value="Lead">Lead</option>
              <option value="Contact">Contact</option>
              <option value="Account">Account</option>
              <option value="Opportunity">Opportunity</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Operation
            </label>
            <select
              value={uploadConfig.operation}
              onChange={(e) =>
                setUploadConfig((prev) => ({
                  ...prev,
                  operation: e.target.value,
                }))
              }
              className="
                w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              "
            >
              <option value="insert">Insert</option>
              <option value="update">Update</option>
              <option value="upsert">Upsert</option>
              <option value="delete">Delete</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              CSV File
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              className="
                w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                file:mr-4 file:py-1 file:px-3
                file:rounded file:border-0
                file:text-sm file:font-medium
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
              "
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Upload a CSV file with Salesforce field names as headers.
          </p>

          <button
            onClick={handleFileUpload}
            disabled={!uploadFile || uploading}
            className="
              px-4 py-2 bg-blue-600 text-white font-medium rounded-lg
              hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors
            "
          >
            {uploading ? "Uploading..." : "Start Bulk Job"}
          </button>
        </div>
      </div>

      {/* Jobs list */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Bulk Jobs</h3>
            <button
              onClick={loadJobs}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="divide-y divide-gray-100">
          {jobs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p>No bulk jobs found.</p>
              <p className="text-sm mt-1">
                Upload a CSV file to create a new bulk job.
              </p>
            </div>
          ) : (
            jobs.map((job) => (
              <div
                key={job.job_id}
                className="p-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => loadJobDetails(job.job_id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        {job.sobject_type}
                      </span>
                      <span className="text-gray-500">-</span>
                      <span className="text-gray-600">{job.operation}</span>
                      <span
                        className={`
                          px-2 py-0.5 text-xs font-medium rounded
                          ${getStatusColor(job.state)}
                        `}
                      >
                        {job.state}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {job.number_records_processed} processed
                      {job.number_records_failed > 0 && (
                        <span className="text-red-600 ml-2">
                          ({job.number_records_failed} failed)
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {(job.state === "Open" ||
                      job.state === "UploadComplete" ||
                      job.state === "InProgress") && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          abortJob(job.job_id);
                        }}
                        className="
                          px-3 py-1 text-sm text-red-600
                          border border-red-200 rounded
                          hover:bg-red-50
                        "
                      >
                        Abort
                      </button>
                    )}
                    <ChevronRightIcon className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Job details modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                Job Details
              </h3>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XIcon className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <dl className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Job ID</dt>
                  <dd className="text-sm text-gray-900 font-mono">
                    {selectedJob.job_id}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd>
                    <span
                      className={`
                        px-2 py-0.5 text-xs font-medium rounded
                        ${getStatusColor(selectedJob.state)}
                      `}
                    >
                      {selectedJob.state}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Records Processed
                  </dt>
                  <dd className="text-sm text-gray-900">
                    {selectedJob.number_records_processed}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Records Failed
                  </dt>
                  <dd className="text-sm text-red-600">
                    {selectedJob.number_records_failed}
                  </dd>
                </div>
              </dl>

              {selectedJob.failed_records.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">
                    Failed Records
                  </h4>
                  <div className="bg-red-50 rounded-lg p-4 max-h-48 overflow-y-auto">
                    <pre className="text-xs text-red-700">
                      {JSON.stringify(selectedJob.failed_records, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 5l7 7-7 7"
      />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  );
}
