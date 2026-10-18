import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { ContractSummaryResponse } from '../api/types';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';
import {
  Plus,
  Search,
  Filter,
  FileCode2,
  Calendar,
  Layers,
  ArrowRight,
  AlertCircle,
} from 'lucide-react';

interface ContractsPageProps {
  onSelectContract: (contractId: string) => void;
  onNavigateToWorkbench: (contractId: string) => void;
}

export const ContractsPage: React.FC<ContractsPageProps> = ({
  onSelectContract,
  onNavigateToWorkbench,
}) => {
  const [contracts, setContracts] = useState<ContractSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'archived'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Create contract modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDescription, setCreateDescription] = useState('');
  const [createChecksJson, setCreateChecksJson] = useState(`[
  {
    "type": "required_fields",
    "fields": ["ticket_id", "status", "priority"]
  },
  {
    "type": "enum",
    "field": "priority",
    "allowed": ["low", "medium", "high", "urgent"]
  }
]`);
  const [createError, setCreateError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchContracts = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = statusFilter === 'all' ? {} : { status: statusFilter };
      const data = await api.listContracts(params);
      setContracts(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch contracts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContracts();
  }, [statusFilter]);

  const handleCreateContract = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    try {
      if (!createName.trim()) {
        throw new Error('Contract name is required.');
      }
      const parsedChecks = JSON.parse(createChecksJson);
      if (!Array.isArray(parsedChecks) || parsedChecks.length === 0) {
        throw new Error('Checks specification must be a non-empty array of check objects.');
      }

      setSubmitting(true);
      const created = await api.createContract({
        name: createName.trim(),
        description: createDescription.trim() || undefined,
        checks: parsedChecks,
      });

      setShowCreateModal(false);
      setCreateName('');
      setCreateDescription('');
      onSelectContract(created.id);
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : 'Invalid configuration');
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = contracts.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.name.toLowerCase().includes(q) ||
      (c.description && c.description.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Declarative Contracts
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage versioned validation contracts defining schemas, constraints, and invariants.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          New Contract
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search contracts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <div className="flex rounded-lg border border-slate-200 p-0.5 bg-slate-50 text-xs">
            {(['all', 'active', 'archived'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1 rounded-md font-medium capitalize transition ${
                  statusFilter === status
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Contracts Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">Loading contracts...</div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
          <FileCode2 className="w-8 h-8 text-slate-400 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-900">No contracts found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {searchQuery
              ? 'No contracts matched your search criteria.'
              : 'Create your first declarative validation contract to begin evaluating AI payloads.'}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 px-3 py-1.5 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg border border-indigo-100"
            >
              + Create Contract
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((c) => (
            <div
              key={c.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h3
                    onClick={() => onSelectContract(c.id)}
                    className="font-bold text-slate-900 hover:text-indigo-600 cursor-pointer text-base line-clamp-1"
                  >
                    {c.name}
                  </h3>
                  <StatusBadge status={c.status} size="sm" />
                </div>
                <p className="text-xs text-slate-500 mt-2 line-clamp-2 min-h-[32px]">
                  {c.description || 'No description provided.'}
                </p>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-500 font-mono">
                  <span className="flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5 text-slate-400" />
                    v{c.latest_version} ({c.total_versions} total)
                  </span>
                  <span className="flex items-center gap-1 text-[11px]">
                    <Calendar className="w-3 h-3 text-slate-400" />
                    {new Date(c.updated_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <button
                    onClick={() => onNavigateToWorkbench(c.id)}
                    className="text-xs font-medium text-slate-600 hover:text-slate-900"
                  >
                    Test run &rarr;
                  </button>
                  <button
                    onClick={() => onSelectContract(c.id)}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                  >
                    Details <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Contract Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Declarative Contract"
      >
        <form onSubmit={handleCreateContract} className="space-y-4">
          {createError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-800 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{createError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Contract Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Support Ticket Generation Contract"
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Description (Optional)
            </label>
            <textarea
              placeholder="Validates support ticket triage schema, severity categories, and required diagnostic fields."
              value={createDescription}
              onChange={(e) => setCreateDescription(e.target.value)}
              rows={2}
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Initial Checks Specification JSON (Array) *
            </label>
            <textarea
              required
              value={createChecksJson}
              onChange={(e) => setCreateChecksJson(e.target.value)}
              rows={8}
              className="w-full font-mono text-xs rounded-lg border border-slate-300 p-3 bg-slate-900 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Create Contract (v1)'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
