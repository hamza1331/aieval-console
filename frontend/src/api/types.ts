export interface CheckSpec {
  type: string;
  field?: string | null;
  severity?: 'info' | 'warning' | 'error' | 'critical' | null;
  [key: string]: unknown;
}

export interface ContractDefinition {
  name: string;
  description?: string | null;
  checks: CheckSpec[];
}

export interface ContractCreateRequest {
  name: string;
  description?: string | null;
  checks: CheckSpec[];
}

export interface ContractUpdateRequest {
  name?: string | null;
  description?: string | null;
  status?: 'active' | 'archived' | null;
}

export interface ContractVersionCreateRequest {
  checks: CheckSpec[];
}

export interface ContractVersionResponse {
  id: string;
  contract_id: string;
  version: number;
  definition_json: ContractDefinition;
  definition_hash: string;
  created_at: string;
}

export interface ContractSummaryResponse {
  id: string;
  name: string;
  description?: string | null;
  status: 'active' | 'archived';
  latest_version: number;
  total_versions: number;
  created_at: string;
  updated_at: string;
}

export interface ContractDetailResponse {
  id: string;
  name: string;
  description?: string | null;
  status: 'active' | 'archived';
  created_at: string;
  updated_at: string;
  versions: ContractVersionResponse[];
}

export interface FailureSchema {
  code: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  path?: string | null;
  metadata?: Record<string, unknown>;
  suggested_repair?: string | null;
}

export interface EvaluationSummarySchema {
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  warnings_count: number;
  duration_ms: number;
}

export interface EvaluationRequest {
  contract_version_id?: string | null;
  contract_id?: string | null;
  contract?: ContractDefinition | null;
  input?: Record<string, unknown> | null;
  output: unknown;
}

export interface EvaluationResponse {
  run_id: string;
  status: 'passed' | 'failed';
  contract_version?: number | null;
  duration_ms: number;
  summary: EvaluationSummarySchema;
  failures: FailureSchema[];
  warnings: FailureSchema[];
}

export interface ReviewResponse {
  id: string;
  run_id: string;
  status: 'unreviewed' | 'reviewed';
  note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewUpdateRequest {
  status?: 'unreviewed' | 'reviewed' | null;
  note?: string | null;
}

export interface RunSummaryResponse {
  id: string;
  contract_id: string;
  contract_name: string;
  contract_version_id: string;
  contract_version_number: number;
  status: 'passed' | 'failed';
  failed_checks: number;
  total_checks: number;
  duration_ms: number;
  review_status: 'unreviewed' | 'reviewed';
  created_at: string;
}

export interface RunDetailResponse {
  id: string;
  contract_id: string;
  contract_name: string;
  contract_version_id: string;
  contract_version_number: number;
  status: 'passed' | 'failed';
  input_json?: Record<string, unknown> | null;
  output_json: unknown;
  result_json: {
    status: 'passed' | 'failed';
    summary: EvaluationSummarySchema;
    failures: FailureSchema[];
    warnings: FailureSchema[];
  };
  duration_ms: number;
  aieval_version: string;
  created_at: string;
  review?: ReviewResponse | null;
}

export interface OverviewResponse {
  total_contracts: number;
  active_contracts: number;
  total_runs: number;
  passed_runs: number;
  failed_runs: number;
  pass_rate: number;
  unreviewed_failures: number;
  recent_runs: RunSummaryResponse[];
}

export interface FixtureValidateRequest {
  fixture: Record<string, unknown>;
}

export interface FixtureValidateResponse {
  valid: boolean;
  error?: string | null;
  checks_count: number;
}

