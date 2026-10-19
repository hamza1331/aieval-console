import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { ContractDiffResponse } from '../api/types';
import { PlusCircle, MinusCircle, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';

interface ContractDiffViewerProps {
  contractId: string;
  fromVersion: number;
  toVersion: number;
}

export const ContractDiffViewer: React.FC<ContractDiffViewerProps> = ({
  contractId,
  fromVersion,
  toVersion,
}) => {
  const [diff, setDiff] = useState<ContractDiffResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .diffContractVersions(contractId, fromVersion, toVersion)
      .then(setDiff)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to compute version difference');
      })
      .finally(() => setLoading(false));
  }, [contractId, fromVersion, toVersion]);

  if (loading) {
    return (
      <div className="py-12 text-center text-xs text-slate-400">
        Comparing version {fromVersion} with version {toVersion}...
      </div>
    );
  }

  if (error || !diff) {
    return (
      <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs">
        {error || 'Unable to compute contract diff.'}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header comparison pill bar */}
      <div className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs">
        <div className="flex items-center gap-2 font-medium text-slate-800">
          <span className="font-mono bg-white px-2 py-0.5 rounded border border-slate-200">
            v{fromVersion}
          </span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-mono bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded border border-indigo-200 font-bold">
            v{toVersion}
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs">
          {diff.added_count > 0 && (
            <span className="text-emerald-700 font-semibold flex items-center gap-1">
              <PlusCircle className="w-3.5 h-3.5" /> +{diff.added_count} added
            </span>
          )}
          {diff.removed_count > 0 && (
            <span className="text-rose-700 font-semibold flex items-center gap-1">
              <MinusCircle className="w-3.5 h-3.5" /> -{diff.removed_count} removed
            </span>
          )}
          {diff.modified_count > 0 && (
            <span className="text-amber-700 font-semibold flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" /> ~{diff.modified_count} modified
            </span>
          )}
          <span className="text-slate-500">{diff.unchanged_count} unchanged</span>
        </div>
      </div>

      {/* Diff items list */}
      <div className="space-y-2.5">
        {diff.checks.map((item, idx) => {
          let cardStyle = 'border-slate-200 bg-white';
          let badgeStyle = 'bg-slate-100 text-slate-700 border-slate-200';
          let Icon = CheckCircle;

          if (item.change_type === 'added') {
            cardStyle = 'border-emerald-200 bg-emerald-50/40';
            badgeStyle = 'bg-emerald-100 text-emerald-800 border-emerald-200';
            Icon = PlusCircle;
          } else if (item.change_type === 'removed') {
            cardStyle = 'border-rose-200 bg-rose-50/40';
            badgeStyle = 'bg-rose-100 text-rose-800 border-rose-200';
            Icon = MinusCircle;
          } else if (item.change_type === 'modified') {
            cardStyle = 'border-amber-200 bg-amber-50/40';
            badgeStyle = 'bg-amber-100 text-amber-800 border-amber-200';
            Icon = AlertCircle;
          }

          return (
            <div
              key={`diff-${idx}`}
              className={`rounded-lg border p-3.5 text-xs transition shadow-2xs ${cardStyle}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`font-semibold uppercase tracking-wider text-[10px] px-2 py-0.5 rounded border flex items-center gap-1 ${badgeStyle}`}
                  >
                    <Icon className="w-3 h-3" />
                    {item.change_type}
                  </span>
                  <span className="font-mono font-bold text-slate-900">{item.check_type}</span>
                  {item.field && (
                    <span className="font-mono text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                      field: {item.field}
                    </span>
                  )}
                </div>
              </div>

              {item.details && item.details.length > 0 && (
                <ul className="mt-2 text-[11px] text-slate-700 space-y-1 list-disc list-inside">
                  {item.details.map((detail, dIdx) => (
                    <li key={`detail-${dIdx}`}>{detail}</li>
                  ))}
                </ul>
              )}

              {item.change_type === 'modified' && item.old_spec && item.new_spec && (
                <div className="mt-2.5 grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div className="p-2 rounded bg-slate-900 text-slate-300">
                    <p className="text-[10px] uppercase text-slate-500 mb-1">Old Spec (v{fromVersion}):</p>
                    <pre className="overflow-x-auto">{JSON.stringify(item.old_spec, null, 2)}</pre>
                  </div>
                  <div className="p-2 rounded bg-slate-900 text-emerald-300">
                    <p className="text-[10px] uppercase text-emerald-500 mb-1">New Spec (v{toVersion}):</p>
                    <pre className="overflow-x-auto">{JSON.stringify(item.new_spec, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

