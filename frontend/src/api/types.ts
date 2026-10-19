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

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
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

export interface FixtureReplayRequest {
  fixture: Record<string, unknown>;
  persist_run?: boolean;
  contract_id?: string | null;
}

export interface FixtureReplayResponse {
  run_id?: string | null;
  actual_status: 'passed' | 'failed';
  expected_status: 'passed' | 'failed';
  parity_status: 'match' | 'regression' | 'divergence';
  matches_expected: boolean;
  failures_count: number;
  duration_ms: number;
  differences: string[];
  failures: FailureSchema[];
}

export interface FixtureImportRequest {
  fixture: Record<string, unknown>;
  contract_name?: string | null;
}

export interface CheckDiffItem {
  check_type: string;
  field?: string | null;
  change_type: 'added' | 'removed' | 'modified' | 'unchanged';
  old_spec?: Record<string, unknown> | null;
  new_spec?: Record<string, unknown> | null;
  details: string[];
}

export interface ContractDiffResponse {
  contract_id: string;
  from_version: number;
  to_version: number;
  added_count: number;
  removed_count: number;
  modified_count: number;
  unchanged_count: number;
  checks: CheckDiffItem[];
}

export interface BatchEvaluationItem {
  item_id?: string | null;
  input?: Record<string, unknown> | null;
  output: unknown;
}

export interface BatchEvaluationRequest {
  contract_version_id?: string | null;
  contract_id?: string | null;
  contract?: ContractDefinition | null;
  items: BatchEvaluationItem[];
}

export interface BatchItemOutcome {
  item_id?: string | null;
  run_id: string;
  status: 'passed' | 'failed';
  failures: FailureSchema[];
  warnings: FailureSchema[];
  duration_ms: number;
}

export interface BatchEvaluationResponse {
  total_items: number;
  passed_count: number;
  failed_count: number;
  pass_rate: number;
  total_duration_ms: number;
  results: BatchItemOutcome[];
}
