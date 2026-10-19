import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { RunSummaryResponse, ContractSummaryResponse } from '../api/types';
import { StatusBadge } from '../components/StatusBadge';
import { RunDetailPage } from './RunDetailPage';
import { FixtureImportModal } from '../components/FixtureImportModal';
import {
  History,
  Filter,
  RefreshCw,
  Search,
  Download,
  Upload,
  Calendar,
  SlidersHorizontal,
  X,
} from 'lucide-react';

interface RunHistoryPageProps {
  initialRunId?: string | null;
  onRunSelected?: (runId: string | null) => void;
}

export const RunHistoryPage: React.FC<RunHistoryPageProps> = ({
  initialRunId,
  onRunSelected,
}) => {
  const [runs, setRuns] = useState<RunSummaryResponse[]>([]);
  const [totalRuns, setTotalRuns] = useState(0);
  const [offset, setOffset] = useState(0);
  const pageSize = 50;
  const [contracts, setContracts] = useState<ContractSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedRunId, setSelectedRunId] = useState<string | null>(initialRunId || null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'passed' | 'failed'>('all');
  const [reviewFilter, setReviewFilter] = useState<'all' | 'unreviewed' | 'reviewed'>('all');
  const [contractFilter, setContractFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Phase 5 Advanced Filters
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [failureCodeFilter, setFailureCodeFilter] = useState<string>('all');
  const [minDuration, setMinDuration] = useState<string>('');
  const [maxDuration, setMaxDuration] = useState<string>('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState<boolean>(false);
  const [showFixtureModal, setShowFixtureModal] = useState<boolean>(false);

  // Fetch contracts for dropdown filter
  useEffect(() => {
    api.listContracts()
      .then((response) => setContracts(response.items))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch contracts');
      });
  }, []);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: Parameters<typeof api.listRuns>[0] = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (reviewFilter !== 'all') params.review_status = reviewFilter;
      if (contractFilter !== 'all') params.contract_id = contractFilter;
      if (fromDate) params.from_date = new Date(fromDate).toISOString();
      if (toDate) params.to_date = new Date(toDate + 'T23:59:59').toISOString();
      if (failureCodeFilter !== 'all') params.failure_code = failureCodeFilter;
      if (minDuration) params.min_duration_ms = Number(minDuration);
      if (maxDuration) params.max_duration_ms = Number(maxDuration);
      params.offset = offset;
      params.limit = pageSize;

      const data = await api.listRuns(params);
      setRuns(data.items);
      setTotalRuns(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch runs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [
    statusFilter,
    reviewFilter,
    contractFilter,
    fromDate,
    toDate,
    failureCodeFilter,
    minDuration,
    maxDuration,
    offset,
  ]);

  useEffect(() => {
    setOffset(0);
  }, [
    statusFilter,
    reviewFilter,
    contractFilter,
    fromDate,
    toDate,
    failureCodeFilter,
    minDuration,
    maxDuration,
  ]);

  const handleResetFilters = () => {
    setOffset(0);
    setStatusFilter('all');
    setReviewFilter('all');
    setContractFilter('all');
    setFromDate('');
    setToDate('');
    setFailureCodeFilter('all');
    setMinDuration('');
    setMaxDuration('');
    setSearchQuery('');
  };

  const handleExport = (format: 'csv' | 'json') => {
    const params: Parameters<typeof api.getExportRunsUrl>[0] = { format };
    if (statusFilter !== 'all') params.status = statusFilter;
    if (reviewFilter !== 'all') params.review_status = reviewFilter;
    if (contractFilter !== 'all') params.contract_id = contractFilter;
    if (fromDate) params.from_date = new Date(fromDate).toISOString();
    if (toDate) params.to_date = new Date(toDate + 'T23:59:59').toISOString();
    if (failureCodeFilter !== 'all') params.failure_code = failureCodeFilter;
    if (minDuration) params.min_duration_ms = Number(minDuration);
    if (maxDuration) params.max_duration_ms = Number(maxDuration);

    const url = api.getExportRunsUrl(params);
    window.open(url, '_blank');
  };

  const handleSelectRun = (id: string | null) => {
    setSelectedRunId(id);
    if (onRunSelected) onRunSelected(id);
  };

  if (selectedRunId) {
    return (
      <RunDetailPage
        runId={selectedRunId}
        onBack={() => handleSelectRun(null)}
      />
    );
  }

  const filteredRuns = runs.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.id.toLowerCase().includes(q) ||
      r.contract_name.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Evaluation Run History</h1>
          <p className="text-sm text-slate-500 mt-1">
            Persisted execution logs, validation diagnostics, and triage review workflows.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Import Fixture Modal Trigger */}
          <button
            onClick={() => setShowFixtureModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition shadow-2xs"
          >
            <Upload className="w-3.5 h-3.5" />
            Import Fixture
          </button>

          {/* Export CSV */}
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition shadow-2xs"
            title="Export filtered runs to CSV format"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            Export CSV
          </button>

          {/* Export JSON */}
          <button
            onClick={() => handleExport('json')}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition shadow-2xs"
            title="Export filtered runs to JSON report"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            Export JSON
          </button>

          {/* Refresh */}
          <button
            onClick={fetchRuns}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition shadow-2xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-72">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by run ID or contract..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            {/* Status filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span>Outcome:</span>
              <select
                value={statusFilter}
                onChange={(e) =>
                  setStatusFilter(e.target.value as 'all' | 'passed' | 'failed')
                }
                className="text-xs bg-slate-50 border border-slate-200 rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium text-slate-700"
              >
                <option value="all">All Outcomes</option>
                <option value="passed">Passed</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            {/* Review status filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <span>Review:</span>
              <select
                value={reviewFilter}
                onChange={(e) =>
                  setReviewFilter(e.target.value as 'all' | 'unreviewed' | 'reviewed')
                }
                className="text-xs bg-slate-50 border border-slate-200 rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium text-slate-700"
              >
                <option value="all">All Reviews</option>
                <option value="unreviewed">Unreviewed</option>
                <option value="reviewed">Reviewed</option>
              </select>
            </div>

            {/* Contract filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <span>Contract:</span>
              <select
                value={contractFilter}
                onChange={(e) => setContractFilter(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium text-slate-700 max-w-[180px] truncate"
              >
                <option value="all">All Contracts</option>
                {contracts.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Advanced Filters Toggle */}
            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-md border transition ${
                showAdvancedFilters || fromDate || toDate || failureCodeFilter !== 'all' || minDuration || maxDuration
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              Advanced
              {(fromDate || toDate || failureCodeFilter !== 'all' || minDuration || maxDuration) && (
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
              )}
            </button>
          </div>
        </div>

        {/* Advanced Filters Tray */}
        {showAdvancedFilters && (
          <div className="pt-3 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs bg-slate-50/50 p-3 rounded-lg">
            <div>
              <label className="block text-slate-600 font-medium mb-1 flex items-center gap-1">
                <Calendar className="w-3 h-3 text-slate-400" /> From Date
              </label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-full text-xs p-1.5 rounded border border-slate-300 bg-white"
              />
            </div>

            <div>
              <label className="block text-slate-600 font-medium mb-1 flex items-center gap-1">
                <Calendar className="w-3 h-3 text-slate-400" /> To Date
              </label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-full text-xs p-1.5 rounded border border-slate-300 bg-white"
              />
            </div>

            <div>
              <label className="block text-slate-600 font-medium mb-1">Failure Code</label>
              <select
                value={failureCodeFilter}
                onChange={(e) => setFailureCodeFilter(e.target.value)}
                className="w-full text-xs p-1.5 rounded border border-slate-300 bg-white font-mono"
              >
                <option value="all">All Failure Codes</option>
                <option value="missing_required_field">MISSING_REQUIRED_FIELD</option>
                <option value="value_constraint_violation">VALUE_CONSTRAINT_VIOLATION</option>
                <option value="regex_mismatch">REGEX_MISMATCH</option>
                <option value="enum_mismatch">ENUM_MISMATCH</option>
                <option value="custom_rule_violation">CUSTOM_RULE_VIOLATION</option>
              </select>
            </div>

            <div className="flex items-end justify-between gap-2">
              <div className="w-1/2">
                <label className="block text-slate-600 font-medium mb-1">Latency (ms)</label>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    placeholder="Min"
                    value={minDuration}
                    onChange={(e) => setMinDuration(e.target.value)}
                    className="w-full text-xs p-1.5 rounded border border-slate-300 bg-white"
                  />
                  <span>-</span>
                  <input
                    type="number"
                    placeholder="Max"
                    value={maxDuration}
                    onChange={(e) => setMaxDuration(e.target.value)}
                    className="w-full text-xs p-1.5 rounded border border-slate-300 bg-white"
                  />
                </div>
              </div>

              <button
                onClick={handleResetFilters}
                className="px-2.5 py-1.5 text-xs text-slate-600 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 rounded flex items-center gap-1 transition"
                title="Reset all filters"
              >
                <X className="w-3 h-3" /> Reset
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Runs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-xs font-medium uppercase text-slate-500 border-b border-slate-100">
              <tr>
                <th className="px-6 py-3.5">Run ID</th>
                <th className="px-6 py-3.5">Contract Target</th>
                <th className="px-6 py-3.5">Version</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Checks Breakdown</th>
                <th className="px-6 py-3.5">Latency</th>
                <th className="px-6 py-3.5">Triage Review</th>
                <th className="px-6 py-3.5">Timestamp</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-normal">
              {loading && (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center text-slate-400">
                    Loading evaluation runs...
                  </td>
                </tr>
              )}

              {!loading && filteredRuns.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center text-slate-400">
                    <History className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    No runs match the selected filters.
                  </td>
                </tr>
              )}

              {filteredRuns.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => handleSelectRun(r.id)}
                  className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-3.5 font-mono text-xs font-semibold text-slate-900">
                    {r.id.slice(0, 10)}...
                  </td>
                  <td className="px-6 py-3.5 font-medium text-slate-900">
                    {r.contract_name}
                  </td>
                  <td className="px-6 py-3.5 font-mono text-xs text-slate-500">
                    v{r.contract_version_number}
                  </td>
                  <td className="px-6 py-3.5">
                    <StatusBadge status={r.status} size="sm" />
                  </td>
                  <td className="px-6 py-3.5 text-xs">
                    <span
                      className={
                        r.failed_checks > 0
                          ? 'text-rose-600 font-semibold'
                          : 'text-slate-600'
                      }
                    >
                      {r.total_checks - r.failed_checks}/{r.total_checks} passed
                    </span>
                  </td>
                  <td className="px-6 py-3.5 font-mono text-xs text-slate-500">
                    {r.duration_ms.toFixed(1)}ms
                  </td>
                  <td className="px-6 py-3.5">
                    <StatusBadge status={r.review_status} size="sm" />
                  </td>
                  <td className="px-6 py-3.5 text-xs text-slate-400 whitespace-nowrap">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-3.5 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectRun(r.id);
                      }}
                      className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                    >
                      Inspect &rarr;
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {!loading && totalRuns > pageSize && (
        <div className="flex items-center justify-between text-xs text-slate-600">
          <span>
            Showing {offset + 1}–{Math.min(offset + runs.length, totalRuns)} of {totalRuns} runs
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - pageSize))}
              className="rounded border border-slate-300 px-3 py-1.5 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={offset + pageSize >= totalRuns}
              onClick={() => setOffset(offset + pageSize)}
              className="rounded border border-slate-300 px-3 py-1.5 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Fixture Import Modal */}
      <FixtureImportModal
        isOpen={showFixtureModal}
        onClose={() => setShowFixtureModal(false)}
        onImportSuccess={() => {
          fetchRuns();
        }}
      />
    </div>
  );
};
