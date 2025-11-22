"use client";

import { useState, useEffect } from "react";
import type { FieldMapping, SobjectDescribe } from "../types";

const SOBJECT_TYPES = ["Lead", "Contact", "Opportunity", "Task"];

/**
 * Salesforce field mapping configuration component.
 *
 * Allows users to customize field mappings between Sales OS and Salesforce.
 */
export function SalesforceFieldMappings() {
  const [selectedSobject, setSelectedSobject] = useState("Lead");
  const [mappings, setMappings] = useState<FieldMapping[]>([]);
  const [salesforceFields, setSalesforceFields] = useState<SobjectDescribe | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadMappings();
    loadSalesforceFields();
  }, [selectedSobject]);

  const loadMappings = async () => {
    try {
      const response = await fetch(`/api/salesforce/mappings/${selectedSobject}`);
      const data = await response.json();
      setMappings(data.mappings || []);
    } catch (error) {
      console.error("Failed to load mappings:", error);
    }
  };

  const loadSalesforceFields = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/salesforce/describe/${selectedSobject}`);
      const data = await response.json();
      setSalesforceFields(data);
    } catch (error) {
      console.error("Failed to load Salesforce fields:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateMapping = (index: number, updates: Partial<FieldMapping>) => {
    setMappings((prev) => {
      const newMappings = [...prev];
      newMappings[index] = { ...newMappings[index], ...updates };
      return newMappings;
    });
  };

  const addMapping = () => {
    setMappings((prev) => [
      ...prev,
      {
        sales_os_field: "",
        salesforce_field: "",
        sobject_type: selectedSobject,
        direction: "bidirectional",
        is_required: false,
      },
    ]);
  };

  const removeMapping = (index: number) => {
    setMappings((prev) => prev.filter((_, i) => i !== index));
  };

  const saveMappings = async () => {
    try {
      setSaving(true);
      const response = await fetch("/api/salesforce/mappings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          org_id: "default",
          mappings,
        }),
      });

      if (response.ok) {
        alert("Mappings saved successfully!");
      }
    } catch (error) {
      console.error("Failed to save mappings:", error);
      alert("Failed to save mappings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Field Mappings
        </h3>
        <p className="text-sm text-gray-600">
          Configure how fields map between Sales OS and Salesforce.
        </p>
      </div>

      {/* Object selector */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">
            Salesforce Object:
          </label>
          <select
            value={selectedSobject}
            onChange={(e) => setSelectedSobject(e.target.value)}
            className="
              px-3 py-2 text-sm border border-gray-300 rounded-lg
              focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            "
          >
            {SOBJECT_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Mappings table */}
      <div className="p-6">
        {loading ? (
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        ) : (
          <>
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm font-medium text-gray-500">
                  <th className="pb-3 pr-4">Sales OS Field</th>
                  <th className="pb-3 pr-4">Salesforce Field</th>
                  <th className="pb-3 pr-4">Direction</th>
                  <th className="pb-3 pr-4">Transform</th>
                  <th className="pb-3 w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {mappings.map((mapping, index) => (
                  <tr key={index}>
                    <td className="py-3 pr-4">
                      <input
                        type="text"
                        value={mapping.sales_os_field}
                        onChange={(e) =>
                          updateMapping(index, { sales_os_field: e.target.value })
                        }
                        placeholder="e.g., first_name"
                        className="
                          w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                          focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        "
                      />
                    </td>
                    <td className="py-3 pr-4">
                      <select
                        value={mapping.salesforce_field}
                        onChange={(e) =>
                          updateMapping(index, { salesforce_field: e.target.value })
                        }
                        className="
                          w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                          focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        "
                      >
                        <option value="">Select field...</option>
                        {salesforceFields?.fields
                          .filter((f) => f.createable || f.updateable)
                          .map((field) => (
                            <option key={field.name} value={field.name}>
                              {field.label} ({field.name})
                            </option>
                          ))}
                      </select>
                    </td>
                    <td className="py-3 pr-4">
                      <select
                        value={mapping.direction}
                        onChange={(e) =>
                          updateMapping(index, {
                            direction: e.target.value as FieldMapping["direction"],
                          })
                        }
                        className="
                          w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                          focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        "
                      >
                        <option value="bidirectional">Bidirectional</option>
                        <option value="outbound">Sales OS to Salesforce</option>
                        <option value="inbound">Salesforce to Sales OS</option>
                      </select>
                    </td>
                    <td className="py-3 pr-4">
                      <select
                        value={mapping.transform || ""}
                        onChange={(e) =>
                          updateMapping(index, {
                            transform: e.target.value || undefined,
                          })
                        }
                        className="
                          w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                          focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        "
                      >
                        <option value="">None</option>
                        <option value="uppercase">Uppercase</option>
                        <option value="lowercase">Lowercase</option>
                        <option value="trim">Trim</option>
                        <option value="date">Date Format</option>
                        <option value="datetime">DateTime Format</option>
                        <option value="phone_e164">Phone E.164</option>
                        <option value="integer">Integer</option>
                        <option value="float">Float</option>
                        <option value="boolean">Boolean</option>
                      </select>
                    </td>
                    <td className="py-3">
                      <button
                        onClick={() => removeMapping(index)}
                        className="p-2 text-gray-400 hover:text-red-500 rounded"
                        title="Remove mapping"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {mappings.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No custom mappings configured. Default mappings will be used.
              </div>
            )}

            <div className="mt-4 flex justify-between">
              <button
                onClick={addMapping}
                className="
                  px-4 py-2 text-sm font-medium text-blue-600
                  border border-blue-200 rounded-lg
                  hover:bg-blue-50 transition-colors
                "
              >
                + Add Mapping
              </button>

              <button
                onClick={saveMappings}
                disabled={saving}
                className="
                  px-4 py-2 bg-blue-600 text-white font-medium rounded-lg
                  hover:bg-blue-700 disabled:opacity-50
                  transition-colors
                "
              >
                {saving ? "Saving..." : "Save Mappings"}
              </button>
            </div>
          </>
        )}
      </div>

      {/* Custom fields section */}
      {salesforceFields && salesforceFields.custom_fields.length > 0 && (
        <div className="p-6 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Available Custom Fields
          </h4>
          <div className="flex flex-wrap gap-2">
            {salesforceFields.custom_fields.map((field) => (
              <span
                key={field.name}
                className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded"
              >
                {field.label} ({field.name})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TrashIcon({ className }: { className?: string }) {
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
        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
      />
    </svg>
  );
}
