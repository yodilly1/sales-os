"use client";

import { useState } from "react";
import type { ConnectionStatus, SalesforceEnvironment } from "../types";

interface Props {
  status: ConnectionStatus | null;
  onConnect: (environment: SalesforceEnvironment) => Promise<void>;
  onDisconnect: () => Promise<void>;
  onRefresh: () => Promise<void>;
}

/**
 * Salesforce connection management card.
 *
 * Displays connection status and provides connect/disconnect functionality.
 */
export function SalesforceConnectionCard({
  status,
  onConnect,
  onDisconnect,
  onRefresh,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [showEnvSelector, setShowEnvSelector] = useState(false);

  const handleConnect = async (env: SalesforceEnvironment) => {
    setLoading(true);
    setShowEnvSelector(false);
    try {
      await onConnect(env);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect from Salesforce?")) {
      return;
    }

    setLoading(true);
    try {
      await onDisconnect();
    } finally {
      setLoading(false);
    }
  };

  if (status?.connected) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm font-medium text-green-700">
                Connected
              </span>
            </div>

            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Salesforce Connected
            </h3>

            <div className="space-y-2 text-sm text-gray-600">
              {status.instance_url && (
                <p>
                  <span className="font-medium">Instance:</span>{" "}
                  <a
                    href={status.instance_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {status.instance_url.replace("https://", "")}
                  </a>
                </p>
              )}

              {status.org_id && (
                <p>
                  <span className="font-medium">Org ID:</span> {status.org_id}
                </p>
              )}

              {status.environment && (
                <p>
                  <span className="font-medium">Environment:</span>{" "}
                  <span
                    className={`
                    inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                    ${
                      status.environment === "production"
                        ? "bg-blue-100 text-blue-800"
                        : "bg-yellow-100 text-yellow-800"
                    }
                  `}
                  >
                    {status.environment === "production"
                      ? "Production"
                      : "Sandbox"}
                  </span>
                </p>
              )}

              {status.user_info && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <p className="font-medium text-gray-900 mb-1">
                    Connected User
                  </p>
                  {status.user_info.name && <p>Name: {status.user_info.name}</p>}
                  {status.user_info.email && (
                    <p>Email: {status.user_info.email}</p>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={onRefresh}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              title="Refresh status"
            >
              <RefreshIcon className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-gray-100">
          <button
            onClick={handleDisconnect}
            disabled={loading}
            className="
              px-4 py-2 text-sm font-medium text-red-600
              border border-red-200 rounded-lg
              hover:bg-red-50 disabled:opacity-50
              transition-colors
            "
          >
            {loading ? "Disconnecting..." : "Disconnect"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-3 h-3 bg-gray-300 rounded-full"></div>
        <span className="text-sm font-medium text-gray-500">Not Connected</span>
      </div>

      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Connect to Salesforce
      </h3>

      <p className="text-sm text-gray-600 mb-6">
        Connect your Salesforce account to sync leads, contacts, opportunities,
        and log activities directly from Sales OS.
      </p>

      {showEnvSelector ? (
        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-700">
            Select your Salesforce environment:
          </p>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => handleConnect("production")}
              disabled={loading}
              className="
                p-4 text-left border border-gray-200 rounded-lg
                hover:border-blue-500 hover:bg-blue-50
                disabled:opacity-50 transition-colors
              "
            >
              <div className="font-medium text-gray-900">Production</div>
              <div className="text-sm text-gray-500">
                Connect to your live Salesforce org
              </div>
            </button>

            <button
              onClick={() => handleConnect("sandbox")}
              disabled={loading}
              className="
                p-4 text-left border border-gray-200 rounded-lg
                hover:border-yellow-500 hover:bg-yellow-50
                disabled:opacity-50 transition-colors
              "
            >
              <div className="font-medium text-gray-900">Sandbox</div>
              <div className="text-sm text-gray-500">
                Connect to a sandbox environment
              </div>
            </button>
          </div>

          <button
            onClick={() => setShowEnvSelector(false)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          onClick={() => setShowEnvSelector(true)}
          disabled={loading}
          className="
            px-4 py-2 bg-blue-600 text-white font-medium rounded-lg
            hover:bg-blue-700 disabled:opacity-50
            transition-colors
          "
        >
          {loading ? "Connecting..." : "Connect to Salesforce"}
        </button>
      )}

      <div className="mt-6 pt-4 border-t border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-2">
          What you can do:
        </h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li className="flex items-center gap-2">
            <CheckIcon className="w-4 h-4 text-green-500" />
            Sync leads and contacts
          </li>
          <li className="flex items-center gap-2">
            <CheckIcon className="w-4 h-4 text-green-500" />
            Update opportunity stages
          </li>
          <li className="flex items-center gap-2">
            <CheckIcon className="w-4 h-4 text-green-500" />
            Log calls and activities
          </li>
          <li className="flex items-center gap-2">
            <CheckIcon className="w-4 h-4 text-green-500" />
            Create tasks and reminders
          </li>
          <li className="flex items-center gap-2">
            <CheckIcon className="w-4 h-4 text-green-500" />
            Bulk import/export data
          </li>
        </ul>
      </div>
    </div>
  );
}

function RefreshIcon({ className }: { className?: string }) {
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
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
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
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}
