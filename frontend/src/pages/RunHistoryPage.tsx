import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { RunSummaryResponse, ContractSummaryResponse } from '../api/types';
import { StatusBadge } from '../components/StatusBadge';
import { RunDetailPage } from './RunDetailPage';
import {
  History,
  Filter,
  RefreshCw,
  Search,
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
  const [contracts, setContracts] = useState<ContractSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedRunId, setSelectedRunId] = useState<string | null>(initialRunId || null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'passed' | 'failed'>('all');
  const [reviewFilter, setReviewFilter] = useState<'all' | 'unreviewed' | 'reviewed'>('all');
  const [contractFilter, setContractFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Fetch contracts for dropdown filter
  useEffect(() => {
    api.listContracts().then(setContracts).catch(() => {});
  }, []);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: { status?: string; contract_id?: string; review_status?: string } = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (reviewFilter !== 'all') params.review_status = reviewFilter;
      if (contractFilter !== 'all') params.contract_id = contractFilter;

      const data = await api.listRuns(params);
      setRuns(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch runs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [statusFilter, reviewFilter, contractFilter]);

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
        <button
          onClick={fetchRuns}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
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
        </div>
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
    </div>
  );
};
