import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare, Send, Radio, Lock, Shield, CheckCircle2,
  AlertTriangle, PhoneOff, UserCheck, Clock, RefreshCw, Zap
} from 'lucide-react';
import { supportTicketsAPI, adminAPI, getWsURL } from '../services/api';
import { useToast } from './MotionComponents';

/**
 * Stage 7 Live Real-Time Chat Panel.
 * Handles single-use WebSocket authentication, application-level JSON ping/pong,
 * live message streaming, internal-note isolation, and presence indicators.
 */
export const LiveChatPanel = ({
  ticketId,
  ticketNumber,
  isLiveChat = false,
  isAdmin = false,
  ticketStatus = 'OPEN',
  initialMessages = [],
  onSessionEnded = null,
  onMessageSent = null,
}) => {
  const { addToast } = useToast();

  const [messages, setMessages] = useState(initialMessages || []);
  const [inputText, setInputText] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [roomOccupancy, setRoomOccupancy] = useState(1);
  const [partnerTyping, setPartnerTyping] = useState(null);
  const [sending, setSending] = useState(false);

  const wsRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Sync initial messages if ticket changes
  useEffect(() => {
    setMessages(initialMessages || []);
  }, [initialMessages]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, partnerTyping]);

  // Connect WebSocket with short-lived single-use ticket
  const connectWebSocket = useCallback(async () => {
    if (!ticketId || isConnected || isConnecting) return;

    try {
      setIsConnecting(true);
      // 1. Authenticated REST request issues single-use connection ticket
      const ticketRes = await supportTicketsAPI.getWSAuthTicket(ticketId);
      const wsUrlRelative = ticketRes.data?.ws_url;
      if (!wsUrlRelative) {
        throw new Error('No WebSocket connection ticket returned');
      }

      const fullWsUrl = getWsURL(wsUrlRelative);
      const ws = new WebSocket(fullWsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        // Start 25-second application-level JSON ping/pong keepalive
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const type = payload.type;
          const data = payload.data;

          if (type === 'new_message' && data) {
            setMessages((prev) => {
              if (prev.some((m) => m.id === data.id)) return prev;
              return [...prev, data];
            });
            if (onMessageSent) onMessageSent(data);
          } else if (type === 'live_accepted') {
            addToast({
              title: 'Agent Joined',
              message: `${data.admin_name || 'An administrator'} has joined the live chat session.`,
              type: 'success',
            });
          } else if (type === 'live_ended') {
            addToast({
              title: 'Live Chat Concluded',
              message: `Live chat session was closed by ${data.ended_by || 'agent'}.`,
              type: 'info',
            });
            if (onSessionEnded) onSessionEnded();
          } else if (type === 'typing' && data) {
            if (data.is_typing) {
              setPartnerTyping(`${data.user_name || 'Agent'} is typing...`);
              if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
              typingTimeoutRef.current = setTimeout(() => {
                setPartnerTyping(null);
              }, 3000);
            } else {
              setPartnerTyping(null);
            }
          } else if (type === 'user_joined' && data) {
            if (data.room_occupancy) setRoomOccupancy(data.room_occupancy);
          } else if (type === 'user_left' && data) {
            if (data.room_occupancy) setRoomOccupancy(data.room_occupancy);
          }
        } catch (e) {
          console.warn('WS message parse error:', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      };

      ws.onerror = (e) => {
        console.error('WebSocket encountered error:', e);
        setIsConnected(false);
        setIsConnecting(false);
      };
    } catch (err) {
      console.error('WebSocket connection error:', err);
      setIsConnecting(false);
      setIsConnected(false);
    }
  }, [ticketId, isConnected, isConnecting, addToast, onSessionEnded, onMessageSent]);

  // Connect on mount or when ticketId changes
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [ticketId]);

  // Handle typing notification
  const handleInputChange = (e) => {
    setInputText(e.target.value);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ type: 'typing', is_typing: true }));
      } catch (err) {
        // ignore
      }
    }
  };

  // Dispatch message via WebSocket or fallback REST
  const handleSendMessage = async (e) => {
    e.preventDefault();
    const content = inputText.trim();
    if (!content || sending) return;

    try {
      setSending(true);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: 'message',
            message: content,
            is_internal: isInternal,
          })
        );
        setInputText('');
      } else {
        // Fallback to REST API if WebSocket is reconnecting
        let res;
        if (isAdmin) {
          res = await adminAPI.sendTicketMessage(ticketId, content, isInternal);
        } else {
          res = await supportTicketsAPI.replyMyTicket(ticketId, content);
        }
        if (res.data) {
          setMessages((prev) => [...prev, res.data]);
          if (onMessageSent) onMessageSent(res.data);
        }
        setInputText('');
      }
    } catch (err) {
      console.error('Failed to dispatch message:', err);
      addToast({
        title: 'Error',
        message: 'Could not send message. Please retry.',
        type: 'error',
      });
    } finally {
      setSending(false);
    }
  };

  // End live handoff session
  const handleEndSession = async () => {
    if (!window.confirm('Are you sure you want to conclude this live chat session?')) return;
    try {
      await supportTicketsAPI.endLiveHandoff(ticketId, 'Session ended by participant');
      addToast({
        title: 'Live Chat Ended',
        message: 'Live chat session has been concluded.',
        type: 'info',
      });
      if (onSessionEnded) onSessionEnded();
    } catch (err) {
      console.error('Failed to end live session:', err);
    }
  };

  return (
    <div className="flex flex-col h-[520px] rounded-2xl bg-black/15 dark:bg-black/30 border border-slate/15 dark:border-rose/15 overflow-hidden font-sans">
      {/* Real-Time Live Header */}
      <div className="p-3.5 bg-slate/10 dark:bg-white/5 border-b border-slate/15 dark:border-rose/15 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="relative flex items-center justify-center">
            <span
              className={`w-3 h-3 rounded-full ${
                isConnected
                  ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50'
                  : isConnecting
                  ? 'bg-amber-500 animate-pulse'
                  : 'bg-rose-500'
              }`}
            />
            {isConnected && (
              <span className="absolute w-3 h-3 rounded-full bg-emerald-400 animate-ping opacity-75" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs text-charcoal dark:text-ivory font-display">
                {ticketNumber} Real-Time Channel
              </span>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                  isConnected
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}
              >
                {isConnected ? 'LIVE WS' : isConnecting ? 'CONNECTING...' : 'DISCONNECTED'}
              </span>
            </div>
            <p className="text-[10px] text-slate/60 font-mono mt-0.5">
              Room participants: {roomOccupancy} {isAdmin && '• Internal notes isolated'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isConnected && (
            <button
              onClick={connectWebSocket}
              disabled={isConnecting}
              className="p-1.5 rounded-lg bg-slate/10 hover:bg-slate/20 text-xs text-slate/70 font-mono flex items-center gap-1"
              title="Reconnect WebSocket"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isConnecting ? 'animate-spin' : ''}`} />
            </button>
          )}

          {isLiveChat && (
            <button
              onClick={handleEndSession}
              className="px-2.5 py-1 rounded-lg bg-rose-500/15 hover:bg-rose-500/25 text-rose-400 border border-rose-500/30 text-[11px] font-mono font-bold flex items-center gap-1 transition"
            >
              <PhoneOff className="w-3 h-3" />
              <span>End Live</span>
            </button>
          )}
        </div>
      </div>

      {/* Message Feed */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 font-sans">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate/50 space-y-2 font-mono text-xs">
            <Radio className="w-8 h-8 text-oxblood dark:text-rose animate-pulse" />
            <p className="font-bold">Real-Time Channel Active</p>
            <p className="text-[11px] max-w-xs text-slate/40">
              Messages stream instantly with sub-second latency across active connections.
            </p>
          </div>
        ) : (
          messages.map((m, idx) => {
            const isMsgAdmin = m.sender_role === 'ADMIN';
            const isNote = Boolean(m.is_internal);

            return (
              <motion.div
                key={m.id || `msg-${idx}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.15 }}
                className={`p-3 rounded-2xl border transition max-w-[85%] ${
                  isNote
                    ? 'bg-amber-500/10 border-amber-500/40 text-amber-200 ml-auto'
                    : isMsgAdmin
                    ? 'bg-oxblood/15 border-oxblood/30 text-charcoal dark:text-ivory ml-auto'
                    : 'bg-slate/10 dark:bg-white/5 border-slate/15 dark:border-rose/15 mr-auto'
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-1 text-[10px] font-mono">
                  <div className="flex items-center gap-1.5 font-bold">
                    {isNote && <Lock className="w-3 h-3 text-amber-400" />}
                    <span
                      className={
                        isNote
                          ? 'text-amber-400'
                          : isMsgAdmin
                          ? 'text-oxblood dark:text-rose'
                          : 'text-slate/70 dark:text-ivory/70'
                      }
                    >
                      {isNote
                        ? `[INTERNAL NOTE] Admin ${m.sender_name || ''}`
                        : isMsgAdmin
                        ? `Support Engineer (${m.sender_name || 'Admin'})`
                        : `${m.sender_name || 'User'}`}
                    </span>
                  </div>
                  <span className="text-slate/40 text-[9px]">
                    {m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                  </span>
                </div>
                <p className="text-xs leading-relaxed whitespace-pre-line font-sans">
                  {m.message}
                </p>
              </motion.div>
            );
          })
        )}

        {partnerTyping && (
          <div className="text-[11px] font-mono text-oxblood dark:text-rose italic flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-oxblood dark:bg-rose animate-bounce" />
            <span className="w-1.5 h-1.5 rounded-full bg-oxblood dark:bg-rose animate-bounce delay-100" />
            <span className="w-1.5 h-1.5 rounded-full bg-oxblood dark:bg-rose animate-bounce delay-200" />
            <span>{partnerTyping}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input / Control Bar */}
      {ticketStatus === 'CLOSED' ? (
        <div className="p-3 bg-slate/10 text-center font-mono text-xs text-slate/50 border-t border-slate/15">
          This ticket is closed. Real-time messaging is inactive.
        </div>
      ) : (
        <form onSubmit={handleSendMessage} className="p-3 bg-slate/10 dark:bg-white/5 border-t border-slate/15 dark:border-rose/15 space-y-2">
          {isAdmin && (
            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 cursor-pointer font-mono text-[11px]">
                <input
                  type="checkbox"
                  checked={isInternal}
                  onChange={(e) => setIsInternal(e.target.checked)}
                  className="rounded text-amber-500 focus:ring-0 bg-transparent"
                />
                <span className={isInternal ? 'text-amber-400 font-bold flex items-center gap-1' : 'text-slate/60'}>
                  <Lock className="w-3 h-3" />
                  <span>Internal Note (Private to Admins)</span>
                </span>
              </label>

              {isInternal && (
                <span className="text-[10px] text-amber-400 font-mono">
                  Hidden from Candidate/Recruiter
                </span>
              )}
            </div>
          )}

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={handleInputChange}
              placeholder={
                isInternal
                  ? 'Type private admin note (never shared with user)...'
                  : 'Type real-time message...'
              }
              className={`flex-1 p-2.5 rounded-xl text-xs text-charcoal dark:text-ivory focus:outline-none transition border ${
                isInternal
                  ? 'bg-amber-500/10 border-amber-500/40 focus:border-amber-400 placeholder:text-amber-300/40'
                  : 'bg-slate/5 dark:bg-white/5 border-slate/20 focus:border-oxblood dark:focus:border-rose'
              }`}
            />

            <button
              type="submit"
              disabled={sending || !inputText.trim()}
              className={`px-4 py-2.5 rounded-xl text-xs font-mono font-bold flex items-center gap-1.5 shrink-0 transition disabled:opacity-40 ${
                isInternal ? 'bg-amber-600 hover:bg-amber-500 text-black' : 'btn-oxblood'
              }`}
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
