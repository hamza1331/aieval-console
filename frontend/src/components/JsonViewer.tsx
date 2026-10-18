import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';

interface JsonViewerProps {
  data: unknown;
  maxHeight?: string;
  title?: string;
}

export const JsonViewer: React.FC<JsonViewerProps> = ({
  data,
  maxHeight = 'max-h-96',
  title,
}) => {
  const [copied, setCopied] = useState(false);
  const jsonString = typeof data === 'string' ? data : JSON.stringify(data, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative rounded-lg border border-slate-200 bg-slate-900 text-slate-100 overflow-hidden shadow-inner">
      {title && (
        <div className="flex items-center justify-between px-3.5 py-2 border-b border-slate-800 bg-slate-950/80 text-xs font-mono text-slate-400">
          <span>{title}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-slate-400 hover:text-slate-200 text-xs py-0.5 px-1.5 rounded bg-slate-800/80 hover:bg-slate-800 transition"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      )}
      {!title && (
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 flex items-center gap-1 text-slate-400 hover:text-slate-200 text-xs py-1 px-2 rounded bg-slate-800/80 hover:bg-slate-800 transition z-10"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      )}
      <pre className={`p-4 text-xs font-mono overflow-auto leading-relaxed ${maxHeight}`}>
        {jsonString}
      </pre>
    </div>
  );
};
