import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  X, 
  Send, 
  Trash2, 
  Brain, 
  Bot, 
  User, 
  RefreshCw, 
  ShieldCheck, 
  Radio, 
  Zap, 
  ChevronRight,
  Flame,
  Droplet
} from 'lucide-react';
import { StationId, CopilotMessage } from '../types';
import { sendCopilotChat, fetchCopilotHistory, clearCopilotHistory } from '../api';

interface CopilotDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeStation: StationId;
}

export const CopilotDrawer: React.FC<CopilotDrawerProps> = ({
  isOpen,
  onClose,
  activeStation,
}) => {
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [historyLoading, setHistoryLoading] = useState<boolean>(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Load chat history
  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const hist = await fetchCopilotHistory();
      if (Array.isArray(hist)) {
        setMessages(hist);
      }
    } catch {
      // Fallback initial welcome
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen, activeStation]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSendMessage = async (customText?: string) => {
    const textToSend = (customText || inputMessage).trim();
    if (!textToSend || loading) return;

    const userMsg: CopilotMessage = {
      message_id: `user-${Date.now()}`,
      role: 'user',
      message: textToSend,
      timestamp: Date.now() / 1000,
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customText) setInputMessage('');
    setLoading(true);

    try {
      const res = await sendCopilotChat(textToSend, activeStation);

      const replyMsg: CopilotMessage = {
        message_id: `friday-${Date.now()}`,
        role: 'assistant',
        message: res.reply || 'Telemetry acknowledged.',
        model_used: res.model_used,
        latency_ms: res.latency_ms,
        cited_sensors: res.cited_sensors,
        suggested_followups: res.suggested_followups,
        timestamp: Date.now() / 1000,
      };

      setMessages((prev) => [...prev, replyMsg]);
    } catch (err: any) {
      const errorMsg: CopilotMessage = {
        message_id: `err-${Date.now()}`,
        role: 'assistant',
        message: `Error contacting F.R.I.D.A.Y. neural bus: ${err.message || 'Groq connection timeout'}. Edge rule engine nominal.`,
        timestamp: Date.now() / 1000,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await clearCopilotHistory();
      setMessages([]);
    } catch {}
  };

  const suggestions = [
    'Assess current microgrid bus stability and frequency',
    'Report Lake Zub utilidor pipe thermal margin',
    'Check Satcom bandwidth and spooled delta frames',
    'What are the active Tier 2 supervised actions?',
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[440px] bg-white/95 backdrop-blur-2xl border-l border-[#eaebf0] shadow-2xl flex flex-col justify-between animate-in slide-in-from-right-8 duration-300">
      {/* 1. Drawer Header */}
      <div className="p-4 sm:p-5 border-b border-[#eaebf0] flex items-center justify-between bg-white/70">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-linear-to-tr from-[#4648d4] to-[#006577] text-white flex items-center justify-center shadow-md shadow-[#4648d4]/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-display font-black text-base text-[#131b2e] tracking-tight">
                Ask F.R.I.D.A.Y. AI
              </h2>
              <span className="px-1.5 py-0.5 rounded-md text-[9px] font-mono font-bold bg-[#ecfdf5] text-[#006c49] border border-[#a7f3d0]">
                10-Agent Society
              </span>
            </div>
            <span className="text-[10px] font-mono text-[#73738c]">
              Target: <strong className="text-[#4648d4] uppercase">{activeStation} Station</strong>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleClearHistory}
            className="p-2 rounded-xl text-[#73738c] hover:text-[#e11d48] hover:bg-[#fff1f2] transition-colors"
            title="Clear Chat History"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-[#73738c] hover:text-[#131b2e] hover:bg-[#f2f3ff] transition-colors"
            title="Close Drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* 2. Messages Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-[#73738c]">
            <div className="w-14 h-14 rounded-3xl bg-[#faf8ff] border border-[#eaedff] flex items-center justify-center text-[#4648d4] mb-3 shadow-xs">
              <Brain className="w-7 h-7" />
            </div>
            <h3 className="font-display font-bold text-base text-[#131b2e] mb-1">
              F.R.I.D.A.Y. Chief Copilot Ready
            </h3>
            <p className="text-xs text-[#73738c] max-w-xs mb-5 leading-relaxed">
              Ask about microgrid frequency, utilidor freeze prevention, active agent consensus, or satcom store-and-forward status.
            </p>

            <div className="w-full space-y-2">
              <span className="text-[10px] font-mono text-[#73738c] uppercase tracking-wider block font-bold text-left">
                Suggested Telemetry Queries:
              </span>
              {suggestions.map((sug, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(sug)}
                  className="w-full p-2.5 rounded-xl bg-[#faf8ff] hover:bg-[#f2f3ff] border border-[#eaedff] text-left text-xs text-[#131b2e] font-medium transition-all flex items-center justify-between group shadow-2xs"
                >
                  <span className="truncate pr-2">{sug}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-[#4648d4] shrink-0 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, idx) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={m.message_id || idx}
              className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-7 h-7 rounded-xl bg-[#4648d4] text-white flex items-center justify-center shrink-0 text-xs font-bold shadow-xs mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                  isUser
                    ? 'bg-[#4648d4] text-white rounded-tr-xs shadow-xs'
                    : 'bg-[#faf8ff] text-[#131b2e] border border-[#eaedff] rounded-tl-xs shadow-2xs'
                }`}
              >
                <div className="font-sans whitespace-pre-wrap">{m.message}</div>

                {!isUser && m.latency_ms && (
                  <div className="mt-2 pt-1.5 border-t border-[#eaedff] flex items-center justify-between text-[9px] font-mono text-[#73738c]">
                    <span>Engine: {m.model_used || 'Groq LPU LLaMA-3.3-70B'}</span>
                    <span className="text-[#006577] font-semibold">{m.latency_ms}ms</span>
                  </div>
                )}
              </div>

              {isUser && (
                <div className="w-7 h-7 rounded-xl bg-[#131b2e] text-white flex items-center justify-center shrink-0 text-xs font-bold shadow-xs mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div className="flex gap-3 justify-start items-center">
            <div className="w-7 h-7 rounded-xl bg-[#4648d4] text-white flex items-center justify-center shrink-0 text-xs font-bold shadow-xs">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff] text-xs text-[#73738c] font-mono flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#4648d4]" />
              <span>F.R.I.D.A.Y. querying 10-agent consensus &amp; telemetry...</span>
            </div>
          </div>
        )}
      </div>

      {/* 3. Input Bench */}
      <div className="p-4 sm:p-5 border-t border-[#eaebf0] bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about microgrid, utilidor, or agents..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-[#faf8ff] border border-[#eaedff] text-xs text-[#131b2e] placeholder-[#73738c] focus:outline-none focus:border-[#4648d4] transition-colors"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || loading}
            className="w-10 h-10 rounded-xl bg-[#4648d4] hover:bg-[#3b3dbf] text-white flex items-center justify-center transition-all disabled:opacity-40 shadow-xs shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
