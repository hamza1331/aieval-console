import React from 'react';
import type { FailureSchema } from '../api/types';
import { StatusBadge } from './StatusBadge';
import { AlertCircle, Wrench, Terminal } from 'lucide-react';

interface FailureListProps {
  failures: FailureSchema[];
  warnings?: FailureSchema[];
}

export const FailureList: React.FC<FailureListProps> = ({ failures, warnings = [] }) => {
  if (failures.length === 0 && warnings.length === 0) {
    return (
      <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4 text-emerald-800 text-sm flex items-center gap-2">
        <span className="font-medium">All checks passed. No failure issues or warnings detected.</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {failures.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-rose-700 flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            Blocking Failures ({failures.length})
          </h4>
          <div className="space-y-2">
            {failures.map((item, index) => (
              <div
                key={`failure-${index}`}
                className="bg-white rounded-lg border border-rose-200 p-4 shadow-sm hover:border-rose-300 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-semibold text-rose-900 bg-rose-50 px-2 py-0.5 rounded border border-rose-100">
                        {item.code}
                      </span>
                      {item.path && (
                        <span className="font-mono text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                          path: <span className="font-bold text-slate-800">{item.path}</span>
                        </span>
                      )}
                      <StatusBadge status={item.severity} size="sm" />
                    </div>
                    <p className="text-sm text-slate-800 font-medium pt-1">{item.message}</p>
                  </div>
                </div>

                {item.suggested_repair && (
                  <div className="mt-3 flex items-start gap-2 bg-amber-50/70 border border-amber-200/80 rounded-md p-2.5 text-xs text-amber-900">
                    <Wrench className="w-3.5 h-3.5 text-amber-600 mt-0.5 shrink-0" />
                    <div>
                      <span className="font-semibold text-amber-950">Suggested Repair: </span>
                      {item.suggested_repair}
                    </div>
                  </div>
                )}

                {item.metadata && Object.keys(item.metadata).length > 0 && (
                  <details className="mt-2 text-xs text-slate-500">
                    <summary className="cursor-pointer hover:text-slate-800 font-mono text-[11px] flex items-center gap-1 py-1">
                      <Terminal className="w-3 h-3" /> Diagnostic Metadata
                    </summary>
                    <pre className="mt-1 bg-slate-900 text-slate-100 p-2.5 rounded font-mono text-[11px] overflow-x-auto">
                      {JSON.stringify(item.metadata, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-700 flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4 text-amber-600" />
            Advisory Warnings ({warnings.length})
          </h4>
          <div className="space-y-2">
            {warnings.map((item, index) => (
              <div
                key={`warning-${index}`}
                className="bg-white rounded-lg border border-amber-200 p-4 shadow-sm"
              >
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="font-mono text-xs font-semibold text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-100">
                    {item.code}
                  </span>
                  {item.path && (
                    <span className="font-mono text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                      path: {item.path}
                    </span>
                  )}
                  <StatusBadge status="warning" size="sm" />
                </div>
                <p className="text-sm text-slate-800">{item.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

