import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toLowerCase();
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  let colors = 'bg-slate-100 text-slate-700 border-slate-200';

  if (normalized === 'passed' || normalized === 'active' || normalized === 'valid') {
    colors = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (normalized === 'failed' || normalized === 'critical') {
    colors = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (normalized === 'error') {
    colors = 'bg-red-50 text-red-700 border-red-200';
  } else if (normalized === 'warning' || normalized === 'unreviewed') {
    colors = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (normalized === 'reviewed') {
    colors = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (normalized === 'archived') {
    colors = 'bg-zinc-100 text-zinc-500 border-zinc-200';
  } else if (normalized === 'info') {
    colors = 'bg-sky-50 text-sky-700 border-sky-200';
  }

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${padding} ${colors}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
          normalized === 'passed' || normalized === 'active' || normalized === 'valid'
            ? 'bg-emerald-500'
            : normalized === 'failed' || normalized === 'critical' || normalized === 'error'
            ? 'bg-rose-500'
            : normalized === 'reviewed'
            ? 'bg-blue-500'
            : normalized === 'unreviewed' || normalized === 'warning'
            ? 'bg-amber-500'
            : 'bg-zinc-400'
        }`}
      />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};
