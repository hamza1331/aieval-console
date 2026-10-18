import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { OverviewResponse } from '../api/types';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import {
  FileCode2,
  PlayCircle,
  History,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';

interface OverviewPageProps {
  onNavigate: (tab: 'overview' | 'contracts' | 'workbench' | 'runs', targetId?: string) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate }) => {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getOverview();
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard overview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Dashboard Overview</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time validation reliability, declarative contracts, and recent evaluation activity.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchOverview}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => onNavigate('workbench')}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition shadow-sm"
          >
            <PlayCircle className="w-4 h-4" />
            Open Workbench
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {/* Metric Cards (FR-11) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Contracts"
          value={data ? `${data.active_contracts} / ${data.total_contracts}` : '-'}
          subtitle="Total declarative contracts"
          icon={FileCode2}
        />
        <MetricCard
          title="Total Runs"
          value={data ? data.total_runs.toLocaleString() : '-'}
          subtitle={`${data?.passed_runs ?? 0} passed, ${data?.failed_runs ?? 0} failed`}
          icon={History}
        />
        <MetricCard
          title="Pass Rate"
          value={data ? `${data.pass_rate}%` : '-'}
          subtitle="Contract compliance rate"
          icon={CheckCircle2}
          variant={data && data.pass_rate >= 80 ? 'success' : 'warning'}
        />
        <MetricCard
          title="Unreviewed Failures"
          value={data ? data.unreviewed_failures : '-'}
          subtitle="Awaiting triage & fixture export"
          icon={AlertTriangle}
          variant={data && data.unreviewed_failures > 0 ? 'danger' : 'default'}
        />
      </div>

      {/* Quick Action Banner */}
      <div className="rounded-xl bg-gradient-to-r from-indigo-900 to-slate-900 text-white p-6 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Test & Validate Output Payloads</h3>
          <p className="text-indigo-200 text-sm mt-1 max-w-xl">
            Evaluate raw LLM completions against declarative contracts with zero code execution.
            Inspect field constraint failures and export golden test fixtures instantly.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => onNavigate('workbench')}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-white text-slate-900 hover:bg-slate-100 transition shadow"
          >
            Run Validation
          </button>
          <button
            onClick={() => onNavigate('contracts')}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-800/80 hover:bg-indigo-800 text-indigo-100 border border-indigo-700 transition"
          >
            Manage Contracts
          </button>
        </div>
      </div>

      {/* Recent Runs Table (FR-11) */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Recent Evaluation Runs</h2>
            <p className="text-xs text-slate-500 mt-0.5">Top 10 most recent validation runs across all contracts</p>
          </div>
          <button
            onClick={() => onNavigate('runs')}
            className="text-xs font-medium text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
          >
            View all runs <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-xs font-medium uppercase text-slate-500 border-b border-slate-100">
              <tr>
                <th className="px-6 py-3">Run ID</th>
                <th className="px-6 py-3">Contract</th>
                <th className="px-6 py-3">Version</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Checks</th>
                <th className="px-6 py-3">Latency</th>
                <th className="px-6 py-3">Review</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-normal">
              {loading && (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-slate-400">
                    Loading runs...
                  </td>
                </tr>
              )}
              {!loading && (!data?.recent_runs || data.recent_runs.length === 0) && (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-slate-400">
                    No evaluation runs recorded yet.
                  </td>
                </tr>
              )}
              {data?.recent_runs.map((run) => (
                <tr key={run.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-6 py-3.5 font-mono text-xs font-semibold text-slate-900">
                    {run.id.slice(0, 10)}...
                  </td>
                  <td className="px-6 py-3.5 font-medium text-slate-900">
                    {run.contract_name}
                  </td>
                  <td className="px-6 py-3.5 font-mono text-xs text-slate-500">
                    v{run.contract_version_number}
                  </td>
                  <td className="px-6 py-3.5">
                    <StatusBadge status={run.status} size="sm" />
                  </td>
                  <td className="px-6 py-3.5 text-xs">
                    <span className={run.failed_checks > 0 ? 'text-rose-600 font-semibold' : 'text-slate-600'}>
                      {run.total_checks - run.failed_checks}/{run.total_checks} passed
                    </span>
                  </td>
                  <td className="px-6 py-3.5 font-mono text-xs text-slate-500">
                    {run.duration_ms.toFixed(1)}ms
                  </td>
                  <td className="px-6 py-3.5">
                    <StatusBadge status={run.review_status} size="sm" />
                  </td>
                  <td className="px-6 py-3.5 text-right">
                    <button
                      onClick={() => onNavigate('runs', run.id)}
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

