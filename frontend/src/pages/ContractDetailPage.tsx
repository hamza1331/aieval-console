import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { ContractDetailResponse, ContractVersionResponse } from '../api/types';
import { StatusBadge } from '../components/StatusBadge';
import { JsonViewer } from '../components/JsonViewer';
import { Modal } from '../components/Modal';
import {
  ArrowLeft,
  Plus,
  PlayCircle,
  Archive,
  CheckCircle,
  Clock,
  Hash,
  FileCode,
  AlertCircle,
} from 'lucide-react';

interface ContractDetailPageProps {
  contractId: string;
  onBack: () => void;
  onNavigateToWorkbench: (contractId: string, versionId?: string) => void;
}

export const ContractDetailPage: React.FC<ContractDetailPageProps> = ({
  contractId,
  onBack,
  onNavigateToWorkbench,
}) => {
  const [contract, setContract] = useState<ContractDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New version modal
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [newVersionJson, setNewVersionJson] = useState('');
  const [versionError, setVersionError] = useState<string | null>(null);
  const [submittingVersion, setSubmittingVersion] = useState(false);

  // Selected version for inspection
  const [selectedVersion, setSelectedVersion] = useState<ContractVersionResponse | null>(null);

  const fetchDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getContract(contractId);
      setContract(data);
      if (data.versions.length > 0) {
        // default select latest version (first in sorted list)
        setSelectedVersion(data.versions[0]);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load contract details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [contractId]);

  const handleToggleStatus = async () => {
    if (!contract) return;
    const newStatus = contract.status === 'active' ? 'archived' : 'active';
    try {
      await api.updateContract(contract.id, { status: newStatus });
      fetchDetail();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to update contract status');
    }
  };

  const handleOpenVersionModal = () => {
    if (selectedVersion) {
      setNewVersionJson(
        JSON.stringify(selectedVersion.definition_json.checks || [], null, 2)
      );
    } else {
      setNewVersionJson('[\n  {\n    "type": "required_fields",\n    "fields": ["ticket_id", "status"]\n  }\n]');
    }
    setVersionError(null);
    setShowVersionModal(true);
  };

  const handleCreateVersion = async (e: React.FormEvent) => {
    e.preventDefault();
    setVersionError(null);
    try {
      const parsed = JSON.parse(newVersionJson);
      if (!Array.isArray(parsed) || parsed.length === 0) {
        throw new Error('Checks specification must be a non-empty array of check objects.');
      }
      setSubmittingVersion(true);
      await api.createContractVersion(contractId, { checks: parsed });
      setShowVersionModal(false);
      await fetchDetail();
    } catch (err: unknown) {
      setVersionError(err instanceof Error ? err.message : 'Invalid JSON or check spec');
    } finally {
      setSubmittingVersion(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        Loading contract specifications...
      </div>
    );
  }

  if (error || !contract) {
    return (
      <div className="space-y-4">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to contracts
        </button>
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error || 'Contract not found'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Contracts
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigateToWorkbench(contract.id, selectedVersion?.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 shadow-sm"
          >
            <PlayCircle className="w-4 h-4" /> Test in Workbench
          </button>
          <button
            onClick={handleToggleStatus}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border shadow-sm transition ${
              contract.status === 'active'
                ? 'bg-white text-slate-700 border-slate-200 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200'
                : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
            }`}
          >
            {contract.status === 'active' ? (
              <>
                <Archive className="w-3.5 h-3.5" /> Archive Contract
              </>
            ) : (
              <>
                <CheckCircle className="w-3.5 h-3.5" /> Activate Contract
              </>
            )}
          </button>
        </div>
      </div>

      {/* Contract Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-slate-900">{contract.name}</h1>
              <StatusBadge status={contract.status} />
            </div>
            <p className="text-sm text-slate-600 mt-1.5">
              {contract.description || 'No description provided.'}
            </p>
          </div>
          <div className="text-xs text-slate-400 font-mono">
            ID: {contract.id}
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-6 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            Created: {new Date(contract.created_at).toLocaleString()}
          </div>
          <div className="flex items-center gap-1.5">
            <FileCode className="w-3.5 h-3.5 text-slate-400" />
            Total Versions: {contract.versions.length}
          </div>
        </div>
      </div>

      {/* Version Management Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Versions Timeline List */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Version History</h3>
            <button
              onClick={handleOpenVersionModal}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-md border border-indigo-100 transition"
            >
              <Plus className="w-3.5 h-3.5" /> New Version
            </button>
          </div>

          <div className="divide-y divide-slate-100 overflow-y-auto max-h-[500px]">
            {contract.versions.map((v) => {
              const isSelected = selectedVersion?.id === v.id;
              const checkCount = v.definition_json?.checks?.length ?? 0;
              return (
                <div
                  key={v.id}
                  onClick={() => setSelectedVersion(v)}
                  className={`p-4 cursor-pointer transition-colors ${
                    isSelected ? 'bg-indigo-50/70 border-l-4 border-indigo-600' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-slate-900 flex items-center gap-1.5">
                      v{v.version}
                      {v.version === contract.versions[0]?.version && (
                        <span className="text-[10px] font-medium bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded">
                          Latest
                        </span>
                      )}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(v.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-xs text-slate-500">
                    <span>{checkCount} checks defined</span>
                    <span className="font-mono text-[11px] text-slate-400 flex items-center gap-0.5">
                      <Hash className="w-3 h-3" />
                      {v.definition_hash.slice(0, 8)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Version Inspector */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          {selectedVersion ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    Definition for Version {selectedVersion.version}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 font-mono">
                    SHA-256: {selectedVersion.definition_hash}
                  </p>
                </div>
                <button
                  onClick={() => onNavigateToWorkbench(contract.id, selectedVersion.id)}
                  className="px-3 py-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 border border-indigo-100 rounded-md"
                >
                  Evaluate against v{selectedVersion.version}
                </button>
              </div>

              <div>
                <p className="text-xs font-medium text-slate-600 mb-2">Checks Specification:</p>
                <JsonViewer
                  data={selectedVersion.definition_json.checks}
                  maxHeight="max-h-[420px]"
                  title={`contract_v${selectedVersion.version}_checks.json`}
                />
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-slate-400 text-sm">
              Select a version from the history list to inspect its definition.
            </div>
          )}
        </div>
      </div>

      {/* New Sequential Version Modal */}
      <Modal
        isOpen={showVersionModal}
        onClose={() => setShowVersionModal(false)}
        title={`Create New Sequential Version (v${(contract.versions[0]?.version ?? 0) + 1})`}
      >
        <form onSubmit={handleCreateVersion} className="space-y-4">
          <p className="text-xs text-slate-500">
            Define declarative check specifications. Versions are sequential, immutable, and SHA-256 hashed.
          </p>

          {versionError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-800 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{versionError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Checks Specification JSON (Array)
            </label>
            <textarea
              value={newVersionJson}
              onChange={(e) => setNewVersionJson(e.target.value)}
              rows={12}
              className="w-full font-mono text-xs rounded-lg border border-slate-300 p-3 bg-slate-900 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setShowVersionModal(false)}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingVersion}
              className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition disabled:opacity-50"
            >
              {submittingVersion ? 'Creating Version...' : 'Create Immutable Version'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

