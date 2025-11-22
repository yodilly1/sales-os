/**
 * TypeScript types for Salesforce integration frontend.
 */

export type SalesforceEnvironment = "production" | "sandbox";

export interface ConnectionStatus {
  connected: boolean;
  instance_url?: string;
  org_id?: string;
  environment?: SalesforceEnvironment;
  user_info?: UserInfo;
}

export interface UserInfo {
  user_id?: string;
  organization_id?: string;
  name?: string;
  email?: string;
  picture?: string;
  nickname?: string;
}

export interface OAuthInitResponse {
  authorization_url: string;
  state: string;
}

export interface FieldMapping {
  sales_os_field: string;
  salesforce_field: string;
  sobject_type: string;
  direction: "inbound" | "outbound" | "bidirectional";
  transform?: string;
  default_value?: unknown;
  is_required: boolean;
}

export interface FieldMappingConfig {
  org_id: string;
  mappings: FieldMapping[];
}

export interface BulkJob {
  job_id: string;
  state: BulkJobStatus;
  sobject_type: string;
  operation: string;
  created_by_id?: string;
  created_date?: string;
  number_records_processed: number;
  number_records_failed: number;
}

export type BulkJobStatus =
  | "Open"
  | "UploadComplete"
  | "InProgress"
  | "JobComplete"
  | "Aborted"
  | "Failed";

export interface BulkJobResult {
  job_id: string;
  state: BulkJobStatus;
  number_records_processed: number;
  number_records_failed: number;
  successful_records: Record<string, unknown>[];
  failed_records: Record<string, unknown>[];
}

export interface SobjectField {
  name: string;
  label: string;
  type: string;
  required: boolean;
  updateable: boolean;
  createable: boolean;
  custom: boolean;
  picklistValues?: PicklistValue[];
}

export interface PicklistValue {
  value: string;
  label: string;
  active: boolean;
  defaultValue: boolean;
}

export interface SobjectDescribe {
  name: string;
  label: string;
  fields: SobjectField[];
  custom_fields: SobjectField[];
}

// Lead types
export interface Lead {
  id: string;
  first_name?: string;
  last_name: string;
  company: string;
  email?: string;
  phone?: string;
  title?: string;
  status: string;
  owner_id?: string;
  created_date?: string;
  last_modified_date?: string;
  is_converted: boolean;
}

export interface CreateLeadRequest {
  first_name?: string;
  last_name: string;
  company: string;
  email?: string;
  phone?: string;
  title?: string;
  website?: string;
  lead_source?: string;
  status?: string;
  description?: string;
  industry?: string;
  custom_fields?: Record<string, unknown>;
}

// Contact types
export interface Contact {
  id: string;
  first_name?: string;
  last_name: string;
  name?: string;
  account_id?: string;
  account_name?: string;
  email?: string;
  phone?: string;
  title?: string;
  owner_id?: string;
  created_date?: string;
  last_modified_date?: string;
}

export interface CreateContactRequest {
  first_name?: string;
  last_name: string;
  account_id?: string;
  email?: string;
  phone?: string;
  title?: string;
  department?: string;
  description?: string;
  lead_source?: string;
  custom_fields?: Record<string, unknown>;
}

// Opportunity types
export interface Opportunity {
  id: string;
  name: string;
  account_id?: string;
  account_name?: string;
  stage_name: string;
  amount?: number;
  close_date?: string;
  probability?: number;
  is_closed: boolean;
  is_won: boolean;
  owner_id?: string;
  created_date?: string;
  last_modified_date?: string;
}

export interface UpdateOpportunityRequest {
  name?: string;
  stage_name?: string;
  amount?: number;
  close_date?: string;
  probability?: number;
  description?: string;
  next_step?: string;
  custom_fields?: Record<string, unknown>;
}

// Task types
export interface Task {
  id: string;
  subject: string;
  what_id?: string;
  who_id?: string;
  owner_id?: string;
  activity_date?: string;
  priority: string;
  status: string;
  is_closed: boolean;
  created_date?: string;
}

export interface AddTaskRequest {
  subject: string;
  what_id?: string;
  who_id?: string;
  owner_id?: string;
  activity_date?: string;
  priority?: "High" | "Normal" | "Low";
  status?: string;
  description?: string;
  is_reminder_set?: boolean;
  reminder_datetime?: string;
  custom_fields?: Record<string, unknown>;
}

// Activity types
export type ActivityType = "Call" | "Email" | "Meeting" | "Other";

export interface LogActivityRequest {
  subject: string;
  what_id?: string;
  who_id?: string;
  activity_type?: ActivityType;
  activity_date?: string;
  duration_minutes?: number;
  description?: string;
  status?: string;
  call_disposition?: string;
  custom_fields?: Record<string, unknown>;
}

// Search types
export interface SearchResult {
  id: string;
  sobject_type: string;
  name?: string;
  attributes: Record<string, unknown>;
}

export interface SearchResponse {
  results: SearchResult[];
  total_size: number;
  done: boolean;
}

// API response types
export interface ApiError {
  detail: string;
  status_code?: number;
}
