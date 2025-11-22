"use client";

import { useState, useEffect } from "react";
import { SalesforceConnectionCard } from "./components/SalesforceConnectionCard";
import { SalesforceFieldMappings } from "./components/SalesforceFieldMappings";
import { SalesforceBulkOperations } from "./components/SalesforceBulkOperations";
import type { ConnectionStatus } from "./types";

/**
 * Salesforce Integration Settings Page
 *
 * Provides UI for:
 * - OAuth2 connection management
 * - Field mapping configuration
 * - Bulk operation monitoring
 */
export default function SalesforceSettingsPage() {
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "connection" | "mappings" | "bulk"
  >("connection");

  // Check connection status on mount
  useEffect(() => {
    checkConnectionStatus();
  }, []);

  // Handle URL params from OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get("connected");
    const error = params.get("error");

    if (connected === "true") {
      checkConnectionStatus();
      // Clean up URL
      window.history.replaceState({}, "", window.location.pathname);
    }

    if (error) {
      console.error("OAuth error:", error);
      // Clean up URL
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const checkConnectionStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/salesforce/status");
      const data = await response.json();
      setConnectionStatus(data);
    } catch (error) {
      console.error("Failed to check connection status:", error);
      setConnectionStatus({ connected: false });
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (environment: "production" | "sandbox") => {
    try {
      const response = await fetch("/api/salesforce/oauth/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ environment }),
      });

      const data = await response.json();

      if (data.authorization_url) {
        // Redirect to Salesforce login
        window.location.href = data.authorization_url;
      }
    } catch (error) {
      console.error("Failed to initiate OAuth:", error);
    }
  };

  const handleDisconnect = async () => {
    try {
      const response = await fetch("/api/salesforce/disconnect", {
        method: "POST",
      });

      if (response.ok) {
        setConnectionStatus({ connected: false });
      }
    } catch (error) {
      console.error("Failed to disconnect:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3 mb-8"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <SalesforceIcon className="w-10 h-10" />
            <h1 className="text-3xl font-bold text-gray-900">
              Salesforce Integration
            </h1>
          </div>
          <p className="text-gray-600">
            Connect your Salesforce CRM to sync leads, contacts, opportunities,
            and activities.
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex gap-8">
            <TabButton
              active={activeTab === "connection"}
              onClick={() => setActiveTab("connection")}
            >
              Connection
            </TabButton>
            <TabButton
              active={activeTab === "mappings"}
              onClick={() => setActiveTab("mappings")}
              disabled={!connectionStatus?.connected}
            >
              Field Mappings
            </TabButton>
            <TabButton
              active={activeTab === "bulk"}
              onClick={() => setActiveTab("bulk")}
              disabled={!connectionStatus?.connected}
            >
              Bulk Operations
            </TabButton>
          </nav>
        </div>

        {/* Content */}
        <div className="space-y-6">
          {activeTab === "connection" && (
            <SalesforceConnectionCard
              status={connectionStatus}
              onConnect={handleConnect}
              onDisconnect={handleDisconnect}
              onRefresh={checkConnectionStatus}
            />
          )}

          {activeTab === "mappings" && connectionStatus?.connected && (
            <SalesforceFieldMappings />
          )}

          {activeTab === "bulk" && connectionStatus?.connected && (
            <SalesforceBulkOperations />
          )}
        </div>
      </div>
    </div>
  );
}

// Tab button component
function TabButton({
  active,
  disabled,
  onClick,
  children,
}: {
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        pb-4 text-sm font-medium border-b-2 transition-colors
        ${
          active
            ? "border-blue-500 text-blue-600"
            : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
        }
        ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
      `}
    >
      {children}
    </button>
  );
}

// Salesforce icon component
function SalesforceIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M20.04 10.92C21.6 9.24 23.76 8.16 26.16 8.16C29.4 8.16 32.16 10.08 33.48 12.84C34.68 12.24 36 11.88 37.44 11.88C42.24 11.88 46.08 15.72 46.08 20.52C46.08 25.32 42.24 29.16 37.44 29.16H37.2C36.6 32.64 33.6 35.28 29.88 35.28C28.44 35.28 27.12 34.92 25.92 34.2C24.6 37.08 21.72 39.12 18.36 39.12C14.52 39.12 11.28 36.48 10.32 32.88C10.08 32.88 9.84 32.88 9.6 32.88C4.68 32.88 0.72 28.92 0.72 24C0.72 19.08 4.68 15.12 9.6 15.12C10.44 15.12 11.28 15.24 12.12 15.48C13.08 12.72 15.84 10.8 19.08 10.8C19.44 10.8 19.68 10.8 20.04 10.92Z"
        fill="#00A1E0"
      />
    </svg>
  );
}
