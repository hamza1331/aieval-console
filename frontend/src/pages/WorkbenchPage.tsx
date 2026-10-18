import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import type {
  ContractSummaryResponse,
  ContractDetailResponse,
  EvaluationResponse,
} from '../api/types';
import { StatusBadge } from '../components/StatusBadge';
import { FailureList } from '../components/FailureList';
import { JsonViewer } from '../components/JsonViewer';
import {
  Play,
  PlayCircle,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  ExternalLink,
  Code2,
  FileCheck,
} from 'lucide-react';

interface WorkbenchPageProps {
  initialContractId?: string | null;
  initialVersionId?: string | null;
  onNavigateToRun?: (runId: string) => void;
}

export const WorkbenchPage: React.FC<WorkbenchPageProps> = ({
  initialContractId,
  initialVersionId,
  onNavigateToRun,
}) => {
  const [contracts, setContracts] = useState<ContractSummaryResponse[]>([]);
  const [selectedContractId, setSelectedContractId] = useState<string>(initialContractId || '');
  const [contractDetail, setContractDetail] = useState<ContractDetailResponse | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState<string>(initialVersionId || '');

  // Mode: stored vs inline
  const [mode, setMode] = useState<'stored' | 'inline'>(initialContractId ? 'stored' : 'stored');

  // Input & Output editors
  const [inputJson, setInputJson] = useState<string>('{\n  "query": "Customer requesting urgent server reboot"\n}');
  const [outputJson, setOutputJson] = useState<string>(`{
  "ticket_id": "TCK-9901",
  "status": "open",
  "priority": "urgent",
  "urgency_score": 9,
  "summary": "Immediate assistance required for primary production database server unresponsive state.",
  "assigned_team": "infrastructure"
}`);

  // Inline contract editor
  const [inlineContractJson, setInlineContractJson] = useState<string>(`{
  "name": "Custom Inline Prototype",
  "description": "Ad-hoc contract test",
  "checks": [
    {
      "type": "required_fields",
      "fields": ["ticket_id", "status", "priority", "summary"]
    },
    {
      "type": "enum",
      "field": "priority",
      "allowed": ["low", "medium", "high", "urgent"]
    },
    {
      "type": "numeric_range",
      "field": "urgency_score",
      "min": 1,
      "max": 10
    }
  ]
}`);

  // Evaluation execution state
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load contracts list
  useEffect(() => {
    api.listContracts({ status: 'active' }).then((list) => {
      setContracts(list);
      if (!selectedContractId && list.length > 0) {
        setSelectedContractId(list[0].id);
      }
    }).catch(() => {
      // Ignore background fetch error
    });
  }, []);

  // When selectedContractId changes, fetch full contract versions
  useEffect(() => {
    if (selectedContractId) {
      api.getContract(selectedContractId).then((detail) => {
        setContractDetail(detail);
        if (!selectedVersionId || !detail.versions.some((v) => v.id === selectedVersionId)) {
          if (detail.versions.length > 0) {
            setSelectedVersionId(detail.versions[0].id);
          }
        }
      }).catch(() => {
        setContractDetail(null);
      });
    } else {
      setContractDetail(null);
    }
  }, [selectedContractId]);

  // Sample presets for quick testing
  const loadPreset = (presetType: 'valid' | 'missing_field' | 'range_error') => {
    if (presetType === 'valid') {
      setOutputJson(`{
  "ticket_id": "TCK-1029",
  "status": "open",
  "priority": "urgent",
  "urgency_score": 8,
  "summary": "Production API response times degraded above 2500ms threshold.",
  "assigned_team": "backend"
}`);
    } else if (presetType === 'missing_field') {
      setOutputJson(`{
  "status": "open",
  "priority": "medium",
  "urgency_score": 5
  /* Missing required ticket_id and summary */
}`);
    } else if (presetType === 'range_error') {
      setOutputJson(`{
  "ticket_id": "TCK-8821",
  "status": "open",
  "priority": "invalid_priority_tier",
  "urgency_score": 45,
  "summary": "Too short"
}`);
    }
  };

  const handleEvaluate = async () => {
    setError(null);
    setEvaluating(true);

    try {
      // Validate output JSON
      let parsedOutput: unknown;
      try {
        parsedOutput = JSON.parse(outputJson);
      } catch {
        throw new Error('AI Output must be valid JSON.');
      }

      // Validate input JSON if present
      let parsedInput: Record<string, unknown> | null = null;
      if (inputJson.trim()) {
        try {
          parsedInput = JSON.parse(inputJson);
        } catch {
          throw new Error('Optional Input context must be valid JSON.');
        }
      }

      let payload;
      if (mode === 'stored') {
        if (!selectedContractId) {
          throw new Error('Please select an active validation contract.');
        }
        payload = {
          contract_id: selectedContractId,
          contract_version_id: selectedVersionId || undefined,
          input: parsedInput,
          output: parsedOutput,
        };
      } else {
        let parsedContract;
        try {
          parsedContract = JSON.parse(inlineContractJson);
        } catch {
          throw new Error('Inline contract must be valid JSON with name and checks array.');
        }
        payload = {
          contract: parsedContract,
          input: parsedInput,
          output: parsedOutput,
        };
      }

      const res = await api.evaluate(payload);
      setEvaluationResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Evaluation failed');
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Evaluation Workbench</h1>
          <p className="text-sm text-slate-500 mt-1">
            Test AI model outputs against declarative validation contracts in real-time.
          </p>
        </div>

        {/* Preset quick buttons */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" /> Presets:
          </span>
          <button
            onClick={() => loadPreset('valid')}
            className="px-2.5 py-1 text-xs font-medium bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded border border-emerald-200 transition"
          >
            Passing
          </button>
          <button
            onClick={() => loadPreset('missing_field')}
            className="px-2.5 py-1 text-xs font-medium bg-rose-50 text-rose-700 hover:bg-rose-100 rounded border border-rose-200 transition"
          >
            Missing Field
          </button>
          <button
            onClick={() => loadPreset('range_error')}
            className="px-2.5 py-1 text-xs font-medium bg-amber-50 text-amber-700 hover:bg-amber-100 rounded border border-amber-200 transition"
          >
            Multi-Failure
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Left editor (inputs/contracts), Right results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (Editors) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Contract Selector Panel */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <FileCheck className="w-4 h-4 text-indigo-600" />
                Validation Contract Target
              </span>
              <div className="flex rounded-lg border border-slate-200 p-0.5 bg-slate-50 text-xs">
                <button
                  onClick={() => setMode('stored')}
                  className={`px-3 py-1 rounded-md font-medium transition ${
                    mode === 'stored'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  Stored Contract
                </button>
                <button
                  onClick={() => setMode('inline')}
                  className={`px-3 py-1 rounded-md font-medium transition ${
                    mode === 'inline'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  Inline Prototyping
                </button>
              </div>
            </div>

            {mode === 'stored' ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">
                    Select Contract
                  </label>
                  <select
                    value={selectedContractId}
                    onChange={(e) => setSelectedContractId(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {contracts.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.status})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">
                    Contract Version
                  </label>
                  <select
                    value={selectedVersionId}
                    onChange={(e) => setSelectedVersionId(e.target.value)}
                    disabled={!contractDetail || contractDetail.versions.length === 0}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-slate-50"
                  >
                    {contractDetail?.versions.map((v) => (
                      <option key={v.id} value={v.id}>
                        v{v.version} (SHA: {v.definition_hash.slice(0, 8)})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1 flex items-center justify-between">
                  <span>Inline Contract JSON (Schema & Checks)</span>
                  <Code2 className="w-3.5 h-3.5 text-slate-400" />
                </label>
                <textarea
                  value={inlineContractJson}
                  onChange={(e) => setInlineContractJson(e.target.value)}
                  rows={8}
                  className="w-full font-mono text-xs rounded-lg border border-slate-300 p-3 bg-slate-900 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            )}
          </div>

          {/* AI Output Payload to Evaluate */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                AI Output Payload (JSON to Validate) *
              </label>
              <span className="text-[11px] text-slate-400 font-mono">Payload &le; 500 KB</span>
            </div>
            <textarea
              value={outputJson}
              onChange={(e) => setOutputJson(e.target.value)}
              rows={11}
              className="w-full font-mono text-xs rounded-lg border border-slate-300 p-3 bg-slate-900 text-emerald-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 leading-relaxed"
            />
          </div>

          {/* Optional Prompt Context / Input JSON */}
          <details className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm text-xs">
            <summary className="font-semibold text-slate-700 cursor-pointer select-none">
              Optional Input / Prompt Context
            </summary>
            <div className="mt-3">
              <textarea
                value={inputJson}
                onChange={(e) => setInputJson(e.target.value)}
                rows={4}
                className="w-full font-mono text-xs rounded-lg border border-slate-300 p-2.5 bg-slate-900 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </details>

          {/* Action Button */}
          <button
            onClick={handleEvaluate}
            disabled={evaluating}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-md flex items-center justify-center gap-2 transition disabled:opacity-60"
          >
            <Play className={`w-4 h-4 fill-white ${evaluating ? 'animate-spin' : ''}`} />
            {evaluating ? 'Running Declarative Evaluation...' : 'Run Evaluation'}
          </button>
        </div>

        {/* Right Column (Results Panel) */}
        <div className="lg:col-span-5 space-y-5">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm min-h-[500px] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <h3 className="font-semibold text-slate-900 text-sm">Evaluation Outcome</h3>
                {evaluationResult && (
                  <StatusBadge status={evaluationResult.status} />
                )}
              </div>

              {!evaluationResult && !evaluating && (
                <div className="py-24 text-center text-slate-400">
                  <PlayCircle className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-sm font-medium text-slate-600">No evaluation run yet</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Click &ldquo;Run Evaluation&rdquo; to test the payload against the contract.
                  </p>
                </div>
              )}

              {evaluating && (
                <div className="py-24 text-center text-slate-400 space-y-3">
                  <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
                  <p className="text-xs font-medium text-slate-600">Executing checks via aieval core...</p>
                </div>
              )}

              {evaluationResult && !evaluating && (
                <div className="space-y-5 pt-4">
                  {/* Stats Pill Row */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-slate-50 border border-slate-100 rounded-lg p-2.5">
                      <p className="text-[11px] text-slate-500 font-medium">Latency</p>
                      <p className="font-mono text-sm font-bold text-slate-900 mt-0.5 flex items-center justify-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        {evaluationResult.duration_ms.toFixed(1)}ms
                      </p>
                    </div>
                    <div className="bg-emerald-50/60 border border-emerald-100 rounded-lg p-2.5">
                      <p className="text-[11px] text-emerald-700 font-medium">Passed</p>
                      <p className="font-mono text-sm font-bold text-emerald-800 mt-0.5 flex items-center justify-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        {evaluationResult.summary.passed_checks} / {evaluationResult.summary.total_checks}
                      </p>
                    </div>
                    <div className="bg-rose-50/60 border border-rose-100 rounded-lg p-2.5">
                      <p className="text-[11px] text-rose-700 font-medium">Failures</p>
                      <p className="font-mono text-sm font-bold text-rose-800 mt-0.5 flex items-center justify-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                        {evaluationResult.summary.failed_checks}
                      </p>
                    </div>
                  </div>

                  {/* Failure List Component */}
                  <div>
                    <FailureList
                      failures={evaluationResult.failures}
                      warnings={evaluationResult.warnings}
                    />
                  </div>

                  {/* Raw Output Result View */}
                  <div className="pt-2">
                    <p className="text-xs font-medium text-slate-600 mb-1.5">Raw Result Output:</p>
                    <JsonViewer
                      data={evaluationResult}
                      maxHeight="max-h-56"
                      title={`run_${evaluationResult.run_id.slice(0, 8)}.json`}
                    />
                  </div>
                </div>
              )}
            </div>

            {evaluationResult && (
              <div className="pt-4 mt-6 border-t border-slate-100 flex items-center justify-between">
                <span className="font-mono text-xs text-slate-400">
                  Run: {evaluationResult.run_id.slice(0, 12)}...
                </span>
                {onNavigateToRun && (
                  <button
                    onClick={() => onNavigateToRun(evaluationResult.run_id)}
                    className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    View in Run History <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
