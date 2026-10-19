import React, { useState } from 'react';
import { api } from '../api/client';
import type { FixtureReplayResponse } from '../api/types';
import { Modal } from './Modal';
import { StatusBadge } from './StatusBadge';
import {
  Upload,
  Play,
  FilePlus,
  CheckCircle,
  AlertTriangle,
  Clock,
  Code,
} from 'lucide-react';

interface FixtureImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess?: (contractId: string) => void;
}

export const FixtureImportModal: React.FC<FixtureImportModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess,
}) => {
  const [jsonText, setJsonText] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [replayLoading, setReplayLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [replayResult, setReplayResult] = useState<FixtureReplayResponse | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setJsonText(content);
      setError(null);
      setReplayResult(null);
    };
    reader.readAsText(file);
  };

  const getParsedFixture = () => {
    if (!jsonText.trim()) throw new Error('Please enter or upload fixture JSON content.');
    try {
      const parsed = JSON.parse(jsonText);
      if (typeof parsed !== 'object' || parsed === null) {
        throw new Error('Fixture must be a JSON object.');
      }
      return parsed;
    } catch (err: unknown) {
      throw new Error(err instanceof Error ? err.message : 'Invalid JSON format');
    }
  };

  const handleReplay = async () => {
    setError(null);
    setReplayResult(null);
    try {
      const fixture = getParsedFixture();
      setReplayLoading(true);
      const res = await api.replayFixture({ fixture, persist_run: false });
      setReplayResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to replay fixture');
    } finally {
      setReplayLoading(false);
    }
  };

  const handleImport = async () => {
    setError(null);
    try {
      const fixture = getParsedFixture();
      setImportLoading(true);
      const res = await api.importFixture({ fixture });
      onClose();
      if (onImportSuccess) {
        onImportSuccess(res.id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to import fixture as contract');
    } finally {
      setImportLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Import & Replay Golden Test Fixture (FR-16)"
      maxWidth="max-w-3xl"
    >
      <div className="space-y-5">
        <p className="text-xs text-slate-500">
          Upload or paste any fixture conforming to <code className="font-mono">FIXTURE_SPEC.md</code>.
          Replay it in real-time to detect regressions against expected outcomes, or import its checks as a permanent contract.
        </p>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* File Upload & Input Area */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
              <Code className="w-3.5 h-3.5 text-indigo-600" /> Fixture JSON Definition
            </label>
            <label className="cursor-pointer text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 bg-indigo-50 px-2.5 py-1 rounded border border-indigo-100">
              <Upload className="w-3.5 h-3.5" /> Upload File (.json)
              <input type="file" accept=".json" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>

          <textarea
            rows={9}
            placeholder='Paste fixture JSON here, e.g. {"name": "fixture", "output": {...}, "checks": [...], "expected": {...}}'
            value={jsonText}
            onChange={(e) => {
              setJsonText(e.target.value);
              setReplayResult(null);
            }}
            className="w-full font-mono text-xs rounded-lg border border-slate-300 p-3 bg-slate-900 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Replay Outcome Card */}
        {replayResult && (
          <div
            className={`rounded-xl border p-4 space-y-3 shadow-xs ${
              replayResult.parity_status === 'match'
                ? 'bg-emerald-50/60 border-emerald-200'
                : replayResult.parity_status === 'regression'
                ? 'bg-rose-50/60 border-rose-300'
                : 'bg-amber-50/60 border-amber-200'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  Parity Status:
                </span>
                <span
                  className={`text-xs font-bold px-2 py-0.5 rounded-full border ${
                    replayResult.parity_status === 'match'
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : replayResult.parity_status === 'regression'
                      ? 'bg-rose-100 text-rose-800 border-rose-300'
                      : 'bg-amber-100 text-amber-800 border-amber-300'
                  }`}
                >
                  {replayResult.parity_status === 'match'
                    ? 'Match (Parity Confirmed)'
                    : replayResult.parity_status === 'regression'
                    ? 'REGRESSION DETECTED'
                    : 'Divergence'}
                </span>
              </div>

              <div className="flex items-center gap-3 text-xs text-slate-600 font-mono">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  {replayResult.duration_ms.toFixed(1)}ms
                </span>
                <StatusBadge status={replayResult.actual_status} size="sm" />
              </div>
            </div>

            {replayResult.differences.length > 0 && (
              <div className="text-xs space-y-1">
                <p className="font-semibold text-slate-900">Discrepancy Details:</p>
                <ul className="list-disc list-inside space-y-0.5 text-slate-700">
                  {replayResult.differences.map((diff, idx) => (
                    <li key={`diff-${idx}`}>{diff}</li>
                  ))}
                </ul>
              </div>
            )}

            {replayResult.matches_expected && (
              <p className="text-xs text-emerald-800 flex items-center gap-1.5 font-medium">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                Evaluation outcome matches expected fixture specification exactly.
              </p>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
          >
            Cancel
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handleReplay}
              disabled={replayLoading || !jsonText.trim()}
              className="px-4 py-2 text-xs font-semibold text-slate-800 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg shadow-xs flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${replayLoading ? 'animate-spin' : ''}`} />
              {replayLoading ? 'Replaying...' : 'Replay Fixture'}
            </button>

            <button
              onClick={handleImport}
              disabled={importLoading || !jsonText.trim()}
              className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <FilePlus className="w-3.5 h-3.5" />
              {importLoading ? 'Importing...' : 'Import as Contract'}
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
