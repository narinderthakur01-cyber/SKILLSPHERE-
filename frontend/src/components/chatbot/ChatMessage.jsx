import React from 'react';
import { Bot, User, Sparkles } from 'lucide-react';

export const ChatMessage = ({ message }) => {
  const isUser = message.sender === 'user';
  const timeFormatted = message.created_at
    ? new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div
      className={`flex items-start gap-2.5 my-2.5 transition-all ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      }`}
    >
      {/* Avatar Icon */}
      <div
        className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs shadow-sm ${
          isUser
            ? 'bg-oxblood text-white'
            : 'bg-emerald-600 text-white'
        }`}
      >
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>

      {/* Message Bubble Container */}
      <div className={`max-w-[82%] sm:max-w-[75%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`px-3.5 py-2.5 rounded-2xl text-xs sm:text-sm leading-relaxed whitespace-pre-wrap break-words shadow-sm ${
            isUser
              ? 'bg-oxblood text-white rounded-tr-xs'
              : 'bg-white dark:bg-charcoal/90 text-charcoal dark:text-ivory border border-oxblood/10 dark:border-white/10 rounded-tl-xs'
          }`}
        >
          {message.content}
        </div>

        {/* Timestamp & Intent Badge (if assistant) */}
        <div className="flex items-center gap-1.5 mt-1 px-1 text-[10px] text-slate/60 dark:text-ivory/40">
          <span>{timeFormatted}</span>
          {!isUser && message.intent && message.intent !== 'fallback' && (
            <span className="inline-flex items-center gap-0.5 text-oxblood dark:text-ivory/60 font-mono text-[9px] bg-oxblood/5 dark:bg-white/5 px-1 py-0.2 rounded">
              <Sparkles className="w-2.5 h-2.5" />
              Verified FAQ
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
