import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { RunDetailResponse } from '../api/types';
import { StatusBadge } from '../components/StatusBadge';
import { FailureList } from '../components/FailureList';
import { JsonViewer } from '../components/JsonViewer';
import { Modal } from '../components/Modal';
import {
  ArrowLeft,
  Clock,
  Download,
  CheckCircle,
  AlertCircle,
  Save,
  MessageSquare,
  FileCheck,
  Check,
} from 'lucide-react';

interface RunDetailPageProps {
  runId: string;
  onBack: () => void;
}

export const RunDetailPage: React.FC<RunDetailPageProps> = ({ runId, onBack }) => {
  const [run, setRun] = useState<RunDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review annotation state (FR-15)
  const [reviewStatus, setReviewStatus] = useState<'unreviewed' | 'reviewed'>('unreviewed');
  const [reviewNote, setReviewNote] = useState<string>('');
  const [savingReview, setSavingReview] = useState(false);
  const [reviewSavedSuccess, setReviewSavedSuccess] = useState(false);

  // Fixture export modal (FR-10, FR-16)
  const [fixtureModalOpen, setFixtureModalOpen] = useState(false);
  const [fixtureData, setFixtureData] = useState<Record<string, unknown> | null>(null);
  const [fixtureValidationResult, setFixtureValidationResult] = useState<{
    valid: boolean;
    error?: string | null;
  } | null>(null);
  const [loadingFixture, setLoadingFixture] = useState(false);

  const fetchRun = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRun(runId);
      setRun(data);
      if (data.review) {
        setReviewStatus(data.review.status);
        setReviewNote(data.review.note || '');
      } else {
        setReviewStatus('unreviewed');
        setReviewNote('');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch run details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRun();
  }, [runId]);

  const handleSaveReview = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingReview(true);
    try {
      const res = await api.updateReview(runId, {
        status: reviewStatus,
        note: reviewNote.trim() || undefined,
      });
      setReviewStatus(res.status);
      setReviewNote(res.note || '');
      setReviewSavedSuccess(true);
      setTimeout(() => setReviewSavedSuccess(false), 2500);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to save review');
    } finally {
      setSavingReview(false);
    }
  };

  const handleOpenFixtureExport = async () => {
    setFixtureModalOpen(true);
    setLoadingFixture(true);
    try {
      const fixture = await api.getRunFixture(runId);
      setFixtureData(fixture);
      // Validate fixture format
      const val = await api.validateFixture({ fixture });
      setFixtureValidationResult(val);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to export fixture');
    } finally {
      setLoadingFixture(false);
    }
  };

  const handleDownloadFixtureFile = () => {
    if (!fixtureData) return;
    const blob = new Blob([JSON.stringify(fixtureData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fixture_${runId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">Loading run evaluation details...</div>
    );
  }

  if (error || !run) {
    return (
      <div className="space-y-4">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to runs
        </button>
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error || 'Evaluation run not found'}
        </div>
      </div>
    );
  }

  const failures = run.result_json?.failures || [];
  const warnings = run.result_json?.warnings || [];
  const summary = run.result_json?.summary;

  return (
    <div className="space-y-6">
      {/* Top back button & action */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Run History
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={handleOpenFixtureExport}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg shadow-sm transition"
          >
            <Download className="w-4 h-4 text-slate-500" />
            Export Golden Fixture (FR-10)
          </button>
        </div>
      </div>

      {/* Run Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-slate-900">Run {run.id.slice(0, 16)}</h1>
              <StatusBadge status={run.status} />
              <StatusBadge status={reviewStatus} />
            </div>
            <p className="text-sm text-slate-600 mt-1">
              Evaluated against{' '}
              <span className="font-semibold text-slate-900">{run.contract_name}</span> (v
              {run.contract_version_number})
            </p>
          </div>

          <div className="text-right">
            <span className="font-mono text-xs text-slate-400 block">ID: {run.id}</span>
            <span className="text-xs text-slate-400 mt-0.5 block">
              Core: aieval v{run.aieval_version}
            </span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-6 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            Timestamp: {new Date(run.created_at).toLocaleString()}
          </div>
          <div className="flex items-center gap-1.5 font-mono">
            <span>Latency: {run.duration_ms.toFixed(1)}ms</span>
          </div>
          {summary && (
            <div className="flex items-center gap-3">
              <span className="text-emerald-700 font-medium">
                {summary.passed_checks} passed
              </span>
              {summary.failed_checks > 0 && (
                <span className="text-rose-700 font-medium">
                  {summary.failed_checks} failed
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 2-Column Content: Left failures & payloads, Right review workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Diagnostics & Payload views */}
        <div className="lg:col-span-8 space-y-6">
          {/* Failure List Section */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
            <h3 className="text-sm font-semibold text-slate-900">Failure Diagnostics & Taxonomy</h3>
            <FailureList failures={failures} warnings={warnings} />
          </div>

          {/* AI Output Section */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">AI Output Evaluated</h3>
              <span className="text-xs text-slate-400 font-mono">Payload inspection</span>
            </div>
            <JsonViewer
              data={run.output_json}
              maxHeight="max-h-72"
              title="output_payload.json"
            />
          </div>

          {/* Optional Prompt Input */}
          {run.input_json && Object.keys(run.input_json).length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
              <h3 className="text-sm font-semibold text-slate-900">Input Context</h3>
              <JsonViewer
                data={run.input_json}
                maxHeight="max-h-48"
                title="prompt_input.json"
              />
            </div>
          )}

          {/* Full Result JSON */}
          <details className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm text-xs">
            <summary className="font-semibold text-slate-700 cursor-pointer select-none">
              Raw Evaluation Result Record
            </summary>
            <div className="mt-3">
              <JsonViewer data={run.result_json} maxHeight="max-h-60" />
            </div>
          </details>
        </div>

        {/* Right Column: Review Workflow (FR-15) & Quick Info */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                <MessageSquare className="w-4 h-4 text-indigo-600" />
                Human Review Workflow
              </h3>
              <StatusBadge status={reviewStatus} size="sm" />
            </div>

            <p className="text-xs text-slate-500">
              Mark this evaluation run as reviewed and record team triage notes or failure root cause annotations.
            </p>

            <form onSubmit={handleSaveReview} className="space-y-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Review Status
                </label>
                <select
                  value={reviewStatus}
                  onChange={(e) =>
                    setReviewStatus(e.target.value as 'unreviewed' | 'reviewed')
                  }
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="unreviewed">Unreviewed</option>
                  <option value="reviewed">Reviewed</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Human Annotation & Triage Notes
                </label>
                <textarea
                  rows={5}
                  placeholder="e.g. Failure confirmed: Model hallucinated unexpected status value instead of enum. Added golden fixture to test regression suite."
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <button
                type="submit"
                disabled={savingReview}
                className="w-full py-2 px-3 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm flex items-center justify-center gap-1.5 transition disabled:opacity-50"
              >
                {reviewSavedSuccess ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-300" />
                    Review Saved!
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    {savingReview ? 'Saving...' : 'Save Review Note'}
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Golden Fixture Callout */}
          <div className="bg-gradient-to-br from-slate-900 to-indigo-950 text-white rounded-xl p-5 shadow-sm space-y-3">
            <h4 className="text-sm font-semibold flex items-center gap-1.5">
              <FileCheck className="w-4 h-4 text-indigo-400" />
              Golden Test Fixture Export
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              Export this run directly into a standardized test fixture conforming to{' '}
              <code className="text-[11px] bg-slate-800 px-1 py-0.5 rounded text-indigo-200">
                FIXTURE_SPEC.md
              </code>
              . Easily commit it into <code className="text-[11px] text-indigo-200">aieval-py/tests/fixtures/</code> for CI regression prevention.
            </p>
            <button
              onClick={handleOpenFixtureExport}
              className="w-full py-2 px-3 text-xs font-semibold text-slate-900 bg-white hover:bg-slate-100 rounded-lg shadow-sm flex items-center justify-center gap-1.5 transition"
            >
              <Download className="w-3.5 h-3.5" />
              Open Fixture Exporter
            </button>
          </div>
        </div>
      </div>

      {/* Export Fixture Modal (FR-10, FR-16) */}
      <Modal
        isOpen={fixtureModalOpen}
        onClose={() => setFixtureModalOpen(false)}
        title="Golden Test Fixture Exporter (FR-10)"
        maxWidth="max-w-3xl"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500">
            Exported fixture structure conforms to <code className="font-mono">FIXTURE_SPEC.md</code> schema, containing inputs, declarative checks, output payload, and expected failure issues.
          </p>

          {loadingFixture ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              Generating and validating fixture payload...
            </div>
          ) : (
            <>
              {fixtureValidationResult && (
                <div
                  className={`p-3 rounded-lg border text-xs flex items-center justify-between ${
                    fixtureValidationResult.valid
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                      : 'bg-rose-50 border-rose-200 text-rose-800'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {fixtureValidationResult.valid ? (
                      <CheckCircle className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-rose-600" />
                    )}
                    <span className="font-medium">
                      {fixtureValidationResult.valid
                        ? 'Fixture schema validation passed (conforms to FIXTURE_SPEC.md).'
                        : `Validation error: ${fixtureValidationResult.error}`}
                    </span>
                  </div>
                  <StatusBadge
                    status={fixtureValidationResult.valid ? 'valid' : 'invalid'}
                    size="sm"
                  />
                </div>
              )}

              <JsonViewer
                data={fixtureData}
                maxHeight="max-h-96"
                title={`golden_fixture_${run.contract_name.toLowerCase().replace(/\s+/g, '_')}_${run.id.slice(0, 8)}.json`}
              />

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setFixtureModalOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Close
                </button>
                <button
                  onClick={handleDownloadFixtureFile}
                  className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm flex items-center gap-1.5 transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download JSON File
                </button>
              </div>
            </>
          )}
        </div>
      </Modal>
    </div>
  );
};

