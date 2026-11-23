import React from 'react';
import { Bot, User, Sparkles, CheckCircle2, AlertTriangle, LifeBuoy, Tag, ArrowRight, Lock } from 'lucide-react';

export const ChatMessage = ({ message, onAction = null }) => {
  const isUser = message.sender === 'user';
  const timeFormatted = message.created_at
    ? new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  const ticketData = message.ticket_data;

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
      <div className={`max-w-[85%] sm:max-w-[78%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`px-3.5 py-2.5 rounded-2xl text-xs sm:text-sm leading-relaxed whitespace-pre-wrap break-words shadow-sm ${
            isUser
              ? 'bg-oxblood text-white rounded-tr-xs'
              : 'bg-white dark:bg-charcoal/90 text-charcoal dark:text-ivory border border-oxblood/10 dark:border-white/10 rounded-tl-xs'
          }`}
        >
          {message.content}

          {/* Interactive Ticket Cards */}
          {ticketData && !isUser && (
            <div className="mt-3 pt-2.5 border-t border-slate/15 dark:border-white/10 font-sans">
              {/* 1. Preview Card */}
              {ticketData.action === 'preview' && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-charcoal dark:text-ivory space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="font-bold flex items-center gap-1 text-amber-500">
                      <LifeBuoy className="w-3.5 h-3.5" />
                      Ticket Confirmation Preview
                    </span>
                    <span className="bg-amber-500/20 text-amber-600 dark:text-amber-400 font-bold px-2 py-0.5 rounded-full text-[10px]">
                      {ticketData.priority || 'HIGH'}
                    </span>
                  </div>

                  <div className="text-[11px] space-y-1 font-mono">
                    <p><span className="text-slate/50">Subject:</span> <span className="font-bold">{ticketData.subject}</span></p>
                    <p><span className="text-slate/50">Category:</span> <span className="font-bold">{ticketData.category}</span></p>
                  </div>

                  {onAction && (
                    <div className="flex items-center gap-2 pt-1 font-mono">
                      <button
                        type="button"
                        onClick={() => onAction('Yes, submit my support ticket', 'confirm_ticket_submission')}
                        className="px-3 py-1.5 rounded-lg bg-oxblood text-white hover:bg-oxblood-dark text-[11px] font-bold transition shadow-xs flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Confirm & Submit</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => onAction('Cancel ticket creation', 'cancel_ticket_creation')}
                        className="px-2.5 py-1.5 rounded-lg bg-black/5 dark:bg-white/10 hover:bg-black/10 text-[11px] font-bold transition"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* 2. Created Success Card */}
              {ticketData.action === 'created' && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-charcoal dark:text-ivory space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="font-bold flex items-center gap-1 text-emerald-500">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Ticket Registered
                    </span>
                    <span className="bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold px-2 py-0.5 rounded-full text-[10px]">
                      {ticketData.status || 'OPEN'}
                    </span>
                  </div>

                  <div className="font-mono text-xs">
                    <p className="text-slate/50 text-[10px]">Reference Number:</p>
                    <p className="font-extrabold text-base text-oxblood dark:text-rose tracking-wider">
                      {ticketData.ticket_number}
                    </p>
                  </div>

                  {onAction && (
                    <div className="pt-1 font-mono">
                      <button
                        type="button"
                        onClick={() => onAction('Where are my support tickets?', 'track_tickets')}
                        className="px-3 py-1.5 rounded-lg bg-slate/10 dark:bg-white/10 hover:bg-oxblood hover:text-white text-[11px] font-bold transition flex items-center gap-1.5"
                      >
                        <span>Track My Tickets</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* 3. Duplicate Prevention Card */}
              {ticketData.action === 'duplicate' && (
                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/30 text-charcoal dark:text-ivory space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="font-bold flex items-center gap-1 text-blue-400">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Active Ticket Exists
                    </span>
                    <span className="font-bold text-oxblood dark:text-rose">
                      {ticketData.ticket_number}
                    </span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-slate/70 dark:text-ivory/70">
                    A support ticket for this issue is already in progress.
                  </p>
                </div>
              )}

              {/* 4. Ticket List Tracker Card */}
              {ticketData.action === 'list' && ticketData.tickets && (
                <div className="space-y-1.5 pt-1">
                  {ticketData.tickets.map((t) => (
                    <div
                      key={t.id || t.ticket_number}
                      className="p-2 rounded-lg bg-slate/5 dark:bg-white/5 border border-slate/10 text-[11px] font-mono flex items-center justify-between gap-2"
                    >
                      <div className="truncate">
                        <span className="font-bold text-oxblood dark:text-rose mr-1.5">{t.ticket_number}</span>
                        <span className="text-charcoal dark:text-ivory font-sans">{t.subject}</span>
                      </div>
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate/15 text-slate/70 shrink-0">
                        {t.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* 5. Live Agent Status Card */}
              {ticketData.action === 'live_agent_status' && (
                <div className="p-3 rounded-xl bg-oxblood/10 border border-oxblood/30 text-charcoal dark:text-ivory space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="font-bold flex items-center gap-1 text-oxblood dark:text-rose">
                      <LifeBuoy className="w-3.5 h-3.5" />
                      Live Agent Desk
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      ticketData.available_admins > 0
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}>
                      {ticketData.available_admins > 0 ? `${ticketData.available_admins} ONLINE` : 'OFFLINE / QUEUED'}
                    </span>
                  </div>
                  {onAction && (
                    <div className="pt-1 font-mono">
                      <button
                        type="button"
                        onClick={() => onAction('Where are my support tickets?', 'track_tickets')}
                        className="px-3 py-1.5 rounded-lg bg-oxblood text-white hover:bg-oxblood-dark text-[11px] font-bold transition flex items-center gap-1.5"
                      >
                        <span>Open Support Tickets</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Timestamp & Intent Badge (if assistant) */}
        <div className="flex items-center gap-1.5 mt-1 px-1 text-[10px] text-slate/60 dark:text-ivory/40">
          <span>{timeFormatted}</span>
          {!isUser && message.intent && message.intent !== 'fallback' && (
            <span className="inline-flex items-center gap-0.5 text-oxblood dark:text-ivory/60 font-mono text-[9px] bg-oxblood/5 dark:bg-white/5 px-1 py-0.2 rounded">
              <Sparkles className="w-2.5 h-2.5" />
              {message.intent.startsWith('troubleshoot') ? 'Guided Troubleshooter' : message.intent.startsWith('ticket') ? 'Support Desk' : 'Verified FAQ'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
