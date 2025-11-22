import { apiClient, uploadFile, ApiClientError } from './client';
import {
  Transcript,
  TranscriptListItem,
  UploadTranscriptRequest,
  UploadTranscriptResponse,
  SPICEDAnalysis,
  CallNotes,
  SuggestedTask,
  CRMPushRequest,
  CRMPushResponse,
  PaginatedResponse,
  ApiResponse,
  ListQueryParams,
} from '@/lib/types';

const TRANSCRIPT_BASE = '/transcript';

/**
 * Transcript API client
 */
export const transcriptApi = {
  /**
   * Get list of transcripts with pagination and filtering
   */
  async list(params?: ListQueryParams): Promise<PaginatedResponse<TranscriptListItem>> {
    const queryParams: Record<string, string | number | boolean | undefined> = {
      page: params?.page,
      pageSize: params?.pageSize,
      search: params?.search,
    };

    if (params?.sort) {
      queryParams.sortField = params.sort.field;
      queryParams.sortDirection = params.sort.direction;
    }

    return apiClient.get<PaginatedResponse<TranscriptListItem>>(TRANSCRIPT_BASE, {
      params: queryParams,
    });
  },

  /**
   * Get a single transcript by ID
   */
  async get(id: string): Promise<Transcript> {
    return apiClient.get<Transcript>(`${TRANSCRIPT_BASE}/${id}`);
  },

  /**
   * Upload a new transcript (text paste)
   */
  async upload(data: UploadTranscriptRequest): Promise<UploadTranscriptResponse> {
    return apiClient.post<UploadTranscriptResponse>(`${TRANSCRIPT_BASE}/upload`, data);
  },

  /**
   * Upload transcript file (txt, vtt, srt)
   */
  async uploadFile(file: File, title: string): Promise<UploadTranscriptResponse> {
    const response = await uploadFile(`${TRANSCRIPT_BASE}/upload/file`, file, { title });
    return response.data as UploadTranscriptResponse;
  },

  /**
   * Sync transcript from Avoma
   */
  async syncFromAvoma(avomaId: string, title?: string): Promise<UploadTranscriptResponse> {
    return apiClient.post<UploadTranscriptResponse>(`${TRANSCRIPT_BASE}/sync/avoma`, {
      avomaId,
      title,
    });
  },

  /**
   * Trigger SPICED analysis
   */
  async analyze(id: string): Promise<{ jobId: string; status: string }> {
    return apiClient.post<{ jobId: string; status: string }>(`${TRANSCRIPT_BASE}/${id}/analyze`);
  },

  /**
   * Get SPICED analysis results
   */
  async getAnalysis(id: string): Promise<SPICEDAnalysis> {
    return apiClient.get<SPICEDAnalysis>(`${TRANSCRIPT_BASE}/${id}/analysis`);
  },

  /**
   * Get call notes
   */
  async getNotes(id: string): Promise<CallNotes> {
    return apiClient.get<CallNotes>(`${TRANSCRIPT_BASE}/${id}/notes`);
  },

  /**
   * Update call notes
   */
  async updateNotes(id: string, content: string): Promise<CallNotes> {
    return apiClient.put<CallNotes>(`${TRANSCRIPT_BASE}/${id}/notes`, { content });
  },

  /**
   * Get suggested tasks
   */
  async getTasks(id: string): Promise<SuggestedTask[]> {
    return apiClient.get<SuggestedTask[]>(`${TRANSCRIPT_BASE}/${id}/tasks`);
  },

  /**
   * Toggle task completion
   */
  async toggleTask(transcriptId: string, taskId: string, completed: boolean): Promise<SuggestedTask> {
    return apiClient.patch<SuggestedTask>(`${TRANSCRIPT_BASE}/${transcriptId}/tasks/${taskId}`, {
      completed,
    });
  },

  /**
   * Push to CRM (HubSpot)
   */
  async pushToCRM(data: CRMPushRequest): Promise<CRMPushResponse> {
    return apiClient.post<CRMPushResponse>(`${TRANSCRIPT_BASE}/${data.transcriptId}/push-crm`, data);
  },

  /**
   * Delete transcript
   */
  async delete(id: string): Promise<void> {
    return apiClient.delete<void>(`${TRANSCRIPT_BASE}/${id}`);
  },

  /**
   * Poll for processing status
   */
  async pollStatus(id: string, maxAttempts = 30, interval = 2000): Promise<Transcript> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      const transcript = await this.get(id);

      if (transcript.status === 'completed' || transcript.status === 'failed') {
        return transcript;
      }

      attempts++;
      await new Promise((resolve) => setTimeout(resolve, interval));
    }

    throw new ApiClientError('Processing timeout', 'TIMEOUT', 408);
  },
};

export { ApiClientError };
