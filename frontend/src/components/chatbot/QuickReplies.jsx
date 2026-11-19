import React from 'react';
import { Sparkles } from 'lucide-react';

export const QuickReplies = ({ quickReplies = [], onSelect, disabled = false }) => {
  if (!quickReplies || quickReplies.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5 my-2">
      {quickReplies.map((qr, index) => (
        <button
          key={`${qr.label}-${index}`}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(qr.query, qr.topic)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full border border-oxblood/20 dark:border-white/15 bg-white/80 dark:bg-charcoal/80 text-oxblood dark:text-ivory hover:bg-oxblood hover:text-white dark:hover:bg-oxblood dark:hover:text-white transition-all duration-150 shadow-2xs hover:shadow-xs active:scale-95 disabled:opacity-50 disabled:pointer-events-none text-left"
        >
          <Sparkles className="w-3 h-3 text-oxblood/70 dark:text-ivory/70 group-hover:text-white shrink-0" />
          <span>{qr.label}</span>
        </button>
      ))}
    </div>
  );
};
