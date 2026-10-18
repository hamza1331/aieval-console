import type {
  ContractCreateRequest,
  ContractDetailResponse,
  ContractSummaryResponse,
  ContractUpdateRequest,
  ContractVersionCreateRequest,
  ContractVersionResponse,
  EvaluationRequest,
  EvaluationResponse,
  FixtureValidateRequest,
  FixtureValidateResponse,
  OverviewResponse,
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

  // Contracts (FR-01, FR-02, FR-03)
  listContracts: (params?: { status?: string; skip?: number; limit?: number }): Promise<ContractSummaryResponse[]> => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.skip !== undefined) query.set('skip', params.skip.toString());
    if (params?.limit !== undefined) query.set('limit', params.limit.toString());
    const qStr = query.toString();
    return request<ContractSummaryResponse[]>(`/contracts${qStr ? `?${qStr}` : ''}`);
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

  // Evaluations / Workbench (FR-04)
  evaluate: (data: EvaluationRequest): Promise<EvaluationResponse> =>
    request<EvaluationResponse>('/evaluations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Runs & Inspection (FR-08, FR-09)
  listRuns: (params?: {
    status?: string;
    contract_id?: string;
    review_status?: string;
    skip?: number;
    limit?: number;
  }): Promise<RunSummaryResponse[]> => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.contract_id) query.set('contract_id', params.contract_id);
    if (params?.review_status) query.set('review_status', params.review_status);
    if (params?.skip !== undefined) query.set('skip', params.skip.toString());
    if (params?.limit !== undefined) query.set('limit', params.limit.toString());
    const qStr = query.toString();
    return request<RunSummaryResponse[]>(`/runs${qStr ? `?${qStr}` : ''}`);
  },

  getRun: (id: string): Promise<RunDetailResponse> => request<RunDetailResponse>(`/runs/${id}`),

  // Human Review (FR-15)
  updateReview: (runId: string, data: ReviewUpdateRequest): Promise<ReviewResponse> =>
    request<ReviewResponse>(`/runs/${runId}/review`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // Fixtures (FR-10, FR-16)
  getRunFixture: (runId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/runs/${runId}/fixture`),

  validateFixture: (data: FixtureValidateRequest): Promise<FixtureValidateResponse> =>
    request<FixtureValidateResponse>('/fixtures/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

