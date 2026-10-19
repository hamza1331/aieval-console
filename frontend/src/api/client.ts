import type {
  BatchEvaluationRequest,
  BatchEvaluationResponse,
  ContractCreateRequest,
  ContractDetailResponse,
  ContractDiffResponse,
  ContractSummaryResponse,
  ContractUpdateRequest,
  ContractVersionCreateRequest,
  ContractVersionResponse,
  EvaluationRequest,
  EvaluationResponse,
  FixtureImportRequest,
  FixtureReplayRequest,
  FixtureReplayResponse,
  FixtureValidateRequest,
  FixtureValidateResponse,
  OverviewResponse,
  PaginatedResponse,
  ReviewResponse,
  ReviewUpdateRequest,
  RunDetailResponse,
  RunSummaryResponse,
} from './types';

const BASE_URL = '/api/v1';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson && typeof errorJson === 'object') {
        errorDetail = errorJson.detail || errorJson.error || JSON.stringify(errorJson);
      }
    } catch {
      // Ignore json parse error and keep statusText
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Overview (FR-11)
  getOverview: (): Promise<OverviewResponse> => request<OverviewResponse>('/overview'),

  // Contracts (FR-01, FR-02, FR-03, Phase 5 Diff)
  listContracts: (params?: {
    status?: string;
    offset?: number;
    limit?: number;
  }): Promise<PaginatedResponse<ContractSummaryResponse>> => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.offset !== undefined) query.set('offset', params.offset.toString());
    if (params?.limit !== undefined) query.set('limit', params.limit.toString());
    const qStr = query.toString();
    return request<PaginatedResponse<ContractSummaryResponse>>(
      `/contracts${qStr ? `?${qStr}` : ''}`
    );
  },

  getContract: (id: string): Promise<ContractDetailResponse> =>
    request<ContractDetailResponse>(`/contracts/${id}`),

  createContract: (data: ContractCreateRequest): Promise<ContractSummaryResponse> =>
    request<ContractSummaryResponse>('/contracts', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateContract: (id: string, data: ContractUpdateRequest): Promise<ContractSummaryResponse> =>
    request<ContractSummaryResponse>(`/contracts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  createContractVersion: (
    id: string,
    data: ContractVersionCreateRequest
  ): Promise<ContractVersionResponse> =>
    request<ContractVersionResponse>(`/contracts/${id}/versions`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  diffContractVersions: (
    id: string,
    fromVersion: number,
    toVersion: number
  ): Promise<ContractDiffResponse> =>
    request<ContractDiffResponse>(
      `/contracts/${id}/diff?from_version=${fromVersion}&to_version=${toVersion}`
    ),

  // Evaluations / Workbench (FR-04, Phase 5 Batch)
  evaluate: (data: EvaluationRequest): Promise<EvaluationResponse> =>
    request<EvaluationResponse>('/evaluations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  evaluateBatch: (data: BatchEvaluationRequest): Promise<BatchEvaluationResponse> =>
    request<BatchEvaluationResponse>('/evaluations/batch', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Runs & Inspection (FR-08, FR-09, Phase 5 Filters & Export)
  listRuns: (params?: {
    status?: string;
    contract_id?: string;
    review_status?: string;
    from_date?: string;
    to_date?: string;
    min_duration_ms?: number;
    max_duration_ms?: number;
    failure_code?: string;
    offset?: number;
    limit?: number;
  }): Promise<PaginatedResponse<RunSummaryResponse>> => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.contract_id) query.set('contract_id', params.contract_id);
    if (params?.review_status) query.set('review_status', params.review_status);
    if (params?.from_date) query.set('from_date', params.from_date);
    if (params?.to_date) query.set('to_date', params.to_date);
    if (params?.min_duration_ms !== undefined)
      query.set('min_duration_ms', params.min_duration_ms.toString());
    if (params?.max_duration_ms !== undefined)
      query.set('max_duration_ms', params.max_duration_ms.toString());
    if (params?.failure_code) query.set('failure_code', params.failure_code);
    if (params?.offset !== undefined) query.set('offset', params.offset.toString());
    if (params?.limit !== undefined) query.set('limit', params.limit.toString());
    const qStr = query.toString();
    return request<PaginatedResponse<RunSummaryResponse>>(`/runs${qStr ? `?${qStr}` : ''}`);
  },

  getRun: (id: string): Promise<RunDetailResponse> => request<RunDetailResponse>(`/runs/${id}`),

  getExportRunsUrl: (params: Record<string, string | number | undefined>): string => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') {
        query.set(k, String(v));
      }
    });
    return `${BASE_URL}/runs/export?${query.toString()}`;
  },

  // Human Review (FR-15)
  updateReview: (runId: string, data: ReviewUpdateRequest): Promise<ReviewResponse> =>
    request<ReviewResponse>(`/runs/${runId}/review`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // Fixtures (FR-10, FR-16, Phase 5 Replay & Import)
  getRunFixture: (runId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/runs/${runId}/fixture`),

  validateFixture: (data: FixtureValidateRequest): Promise<FixtureValidateResponse> =>
    request<FixtureValidateResponse>('/fixtures/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  replayFixture: (data: FixtureReplayRequest): Promise<FixtureReplayResponse> =>
    request<FixtureReplayResponse>('/fixtures/replay', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  importFixture: (data: FixtureImportRequest): Promise<ContractSummaryResponse> =>
    request<ContractSummaryResponse>('/fixtures/import', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
