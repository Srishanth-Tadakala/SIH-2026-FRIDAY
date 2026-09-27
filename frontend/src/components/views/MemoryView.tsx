import React, { useState, useEffect, useCallback } from 'react';
import { 
  Database, 
  Search, 
  Filter, 
  Brain, 
  Sparkles, 
  RefreshCw, 
  Clock, 
  Tag, 
  Layers, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  ChevronRight, 
  Plus, 
  Terminal,
  Activity,
  X
} from 'lucide-react';
import { StationId } from '../../types';
import { 
  MemoryRecord, 
  MemoryStatsSummary, 
  MemoryRetrievalEvent,
  fetchMemories, 
  fetchMemoryStats, 
  fetchMemoryRetrievalEvents,
  searchMemories,
  createMemory,
  MemoryType
} from '../../api/memory';

interface MemoryViewProps {
  activeStation: StationId;
}

export const MemoryView: React.FC<MemoryViewProps> = ({ activeStation }) => {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [stats, setStats] = useState<MemoryStatsSummary | null>(null);
  const [retrievalEvents, setRetrievalEvents] = useState<MemoryRetrievalEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searching, setSearching] = useState<boolean>(false);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedAgent, setSelectedAgent] = useState<string>('ALL');
  const [selectedStation, setSelectedStation] = useState<string>(activeStation);
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [activeTab, setActiveTab] = useState<'records' | 'retrievals'>('records');

  // Detail Drawer
  const [selectedRecord, setSelectedRecord] = useState<MemoryRecord | null>(null);
  
  // Create Modal
  const [createModalOpen, setCreateModalOpen] = useState<boolean>(false);
  const [newTitle, setNewTitle] = useState('');
  const [newSummary, setNewSummary] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newType, setNewType] = useState<MemoryType>('SOP');
  const [newAgent, setNewAgent] = useState('PLANNING');
  const [newSeverity, setNewSeverity] = useState<'INFO' | 'WARNING' | 'CRITICAL'>('INFO');
  const [newTags, setNewTags] = useState('sop, contingency, polar-twin');
  const [creating, setCreating] = useState(false);

  // Load Data from Real Backend
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [mems, st, evts] = await Promise.all([
        fetchMemories({
          agent_role: selectedAgent !== 'ALL' ? selectedAgent : undefined,
          station_id: selectedStation !== 'ALL' ? selectedStation : undefined,
          memory_type: selectedType !== 'ALL' ? selectedType : undefined,
          severity: selectedSeverity !== 'ALL' ? selectedSeverity : undefined,
          query: searchQuery ? searchQuery : undefined,
          limit: 100,
        }),
        fetchMemoryStats().catch(() => null),
        fetchMemoryRetrievalEvents(30).catch(() => []),
      ]);
      setMemories(mems || []);
      if (st) setStats(st);
      if (evts) setRetrievalEvents(evts);
    } catch (err) {
      console.error('Failed to load persistent memories:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedAgent, selectedStation, selectedType, selectedSeverity, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle Search Submission
  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      loadData();
      return;
    }
    setSearching(true);
    try {
      const res = await searchMemories({
        query: searchQuery,
        agent_role: selectedAgent !== 'ALL' ? selectedAgent : undefined,
        station_id: selectedStation !== 'ALL' ? selectedStation : undefined,
        limit: 50,
      });
      setMemories(res.memories || []);
      if (res.retrieval_event) {
        setRetrievalEvents((prev) => [res.retrieval_event, ...prev.slice(0, 29)]);
      }
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  // Handle Create Memory Record
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;
    setCreating(true);
    try {
      await createMemory({
        title: newTitle,
        summary: newSummary || newTitle,
        content: newContent,
        memory_type: newType,
        agent_role: newAgent,
        station_id: selectedStation !== 'ALL' ? selectedStation : 'bharati',
        severity: newSeverity,
        source: 'OPERATOR_CONSOLE',
        tags: newTags.split(',').map((t) => t.trim()).filter(Boolean),
      });
      setCreateModalOpen(false);
      setNewTitle('');
      setNewSummary('');
      setNewContent('');
      await loadData();
    } catch (err) {
      alert('Failed to persist memory record to backend.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="w-full space-y-6 pb-12">
      {/* View Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-[#eaebf0]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10b981] animate-pulse" />
            <h1 className="font-display font-black text-2xl text-[#131b2e] tracking-tight">
              Persistent Cognitive Memory &amp; Knowledge Subsystem
            </h1>
          </div>
          <p className="text-xs text-[#73738c] font-mono">
            Directly connected to PostgreSQL persistence layer with real-time vector embeddings and agent context injection.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => loadData()}
            className="px-3 py-2 rounded-xl bg-white border border-[#eaebf0] hover:bg-[#faf8ff] text-xs font-mono font-semibold flex items-center gap-1.5 transition-all text-[#131b2e] cursor-pointer shadow-xs"
            title="Refresh memory store"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#4648d4] ${loading ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </button>

          <button
            onClick={() => setCreateModalOpen(true)}
            className="px-3.5 py-2 rounded-xl bg-[#4648d4] hover:bg-[#3b3dbf] text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Store Memory</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#73738c] font-mono">Total Memories</span>
            <Database className="w-4 h-4 text-[#4648d4]" />
          </div>
          <div className="font-mono font-black text-2xl text-[#131b2e]">
            {stats ? stats.total_memories : (loading ? '—' : '0')}
          </div>
          <span className="text-[10px] text-[#73738c] font-mono">
            {stats ? `${Object.keys(stats.counts_by_agent || {}).length} active agent partitions` : 'Querying backend...'}
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#73738c] font-mono">Retrieval Queries</span>
            <Brain className="w-4 h-4 text-[#10b981]" />
          </div>
          <div className="font-mono font-black text-2xl text-[#131b2e]">
            {stats ? stats.total_retrieval_events : (loading ? '—' : '0')}
          </div>
          <span className="text-[10px] text-[#73738c] font-mono">
            Agent context injections logged
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#73738c] font-mono">Avg Retrieval Latency</span>
            <Clock className="w-4 h-4 text-[#f59e0b]" />
          </div>
          <div className="font-mono font-black text-2xl text-[#131b2e]">
            {stats && stats.average_retrieval_latency_ms != null ? `${stats.average_retrieval_latency_ms.toFixed(1)} ms` : '—'}
          </div>
          <span className="text-[10px] text-[#73738c] font-mono">
            Cosine similarity + partition filter
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#73738c] font-mono">Storage Engine</span>
            <Activity className="w-4 h-4 text-[#006577]" />
          </div>
          <div className="font-mono font-black text-base text-[#131b2e]">
            POSTGRESQL / STORE
          </div>
          <span className="text-[10px] text-[#006c49] font-mono font-semibold">
            ACID Durable • Survives Restart
          </span>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-[#73738c]" />
            <input
              type="text"
              placeholder="Search persistent memories by title, symptom, SOP, or semantic tag..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-[#eaebf0] bg-[#faf8ff] text-xs font-mono focus:outline-hidden focus:border-[#4648d4] text-[#131b2e]"
            />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="px-4 py-2 bg-[#4648d4] text-white rounded-xl text-xs font-mono font-bold hover:bg-[#3b3dbf] transition-all cursor-pointer flex items-center gap-1.5"
          >
            {searching ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>Semantic Search</span>
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#f4f4f5]">
          <div className="flex items-center gap-1 text-xs text-[#73738c] font-mono mr-2">
            <Filter className="w-3.5 h-3.5" />
            <span>Filters:</span>
          </div>

          {/* Station Filter */}
          <select
            value={selectedStation}
            onChange={(e) => setSelectedStation(e.target.value)}
            className="px-2.5 py-1 rounded-lg border border-[#eaebf0] bg-[#faf8ff] text-xs font-mono text-[#131b2e]"
          >
            <option value="ALL">All Stations</option>
            <option value="bharati">Bharati Station</option>
            <option value="maitri">Maitri Station</option>
          </select>

          {/* Agent Role Filter */}
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="px-2.5 py-1 rounded-lg border border-[#eaebf0] bg-[#faf8ff] text-xs font-mono text-[#131b2e]"
          >
            <option value="ALL">All 10 Agents</option>
            <option value="PLANNING">Planning Agent</option>
            <option value="DIAGNOSTIC">Diagnostic Agent</option>
            <option value="SITUATION_AWARENESS">Situation Awareness</option>
            <option value="LIFE_SUPPORT">Life Support Agent</option>
            <option value="ENERGY">Energy & Microgrid</option>
            <option value="THERMAL">Thermal Agent</option>
            <option value="SATCOM">Satcom Agent</option>
            <option value="EDGE">Edge Coordinator</option>
            <option value="STRUCTURAL">Structural Health</option>
            <option value="CHIEF_ORCHESTRATOR">Chief Orchestrator</option>
          </select>

          {/* Memory Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-2.5 py-1 rounded-lg border border-[#eaebf0] bg-[#faf8ff] text-xs font-mono text-[#131b2e]"
          >
            <option value="ALL">All Types</option>
            <option value="SOP">SOP (Standard Operating Proc)</option>
            <option value="INCIDENT">Incident Episode</option>
            <option value="AGENT">Agent-Scoped</option>
            <option value="STATION">Station-Scoped</option>
            <option value="GLOBAL">Global Policy</option>
            <option value="OPERATOR">Operator Action</option>
          </select>

          {/* Severity Filter */}
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-2.5 py-1 rounded-lg border border-[#eaebf0] bg-[#faf8ff] text-xs font-mono text-[#131b2e]"
          >
            <option value="ALL">All Severities</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="CRITICAL">Critical</option>
          </select>

          {(selectedAgent !== 'ALL' || selectedStation !== 'ALL' || selectedType !== 'ALL' || selectedSeverity !== 'ALL' || searchQuery) && (
            <button
              onClick={() => {
                setSelectedAgent('ALL');
                setSelectedStation('ALL');
                setSelectedType('ALL');
                setSelectedSeverity('ALL');
                setSearchQuery('');
              }}
              className="text-xs text-[#e11d48] font-mono hover:underline ml-auto"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#eaebf0] gap-4">
        <button
          onClick={() => setActiveTab('records')}
          className={`pb-2.5 text-xs font-mono font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
            activeTab === 'records'
              ? 'border-[#4648d4] text-[#4648d4]'
              : 'border-transparent text-[#73738c] hover:text-[#131b2e]'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>Persistent Records ({memories.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('retrievals')}
          className={`pb-2.5 text-xs font-mono font-bold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
            activeTab === 'retrievals'
              ? 'border-[#4648d4] text-[#4648d4]'
              : 'border-transparent text-[#73738c] hover:text-[#131b2e]'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Live Agent Retrieval Telemetry ({retrievalEvents.length})</span>
        </button>
      </div>

      {/* Content Area */}
      {activeTab === 'records' && (
        <div className="space-y-3">
          {memories.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-white border border-[#eaebf0] space-y-2">
              <Database className="w-8 h-8 text-[#73738c] mx-auto opacity-50" />
              <h3 className="font-display font-bold text-sm text-[#131b2e]">0 memories found</h3>
              <p className="text-xs text-[#73738c] font-mono">
                No persistent cognitive memory records match the selected criteria.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {memories.map((rec) => (
                <div
                  key={rec.memory_id}
                  onClick={() => setSelectedRecord(rec)}
                  className="p-4 rounded-2xl bg-white border border-[#eaebf0] hover:border-[#4648d4] shadow-xs hover:shadow-md transition-all cursor-pointer group text-left flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                          rec.severity === 'CRITICAL' ? 'bg-[#fff1f2] text-[#e11d48] border border-[#fecdd3]' :
                          rec.severity === 'WARNING' ? 'bg-[#fffbeb] text-[#d97706] border border-[#fde68a]' :
                          'bg-[#faf8ff] text-[#4648d4] border border-[#eaedff]'
                        }`}>
                          {rec.severity}
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-[#f4f4f5] text-[#71717a] text-[10px] font-mono">
                          {rec.memory_type}
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-[#ecfeff] text-[#006577] text-[10px] font-mono">
                          {rec.station_id.toUpperCase()}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-[#73738c]">
                        {rec.memory_id}
                      </span>
                    </div>

                    <h4 className="font-display font-bold text-sm text-[#131b2e] group-hover:text-[#4648d4] transition-colors mb-1 line-clamp-1">
                      {rec.title}
                    </h4>

                    <p className="text-xs text-[#73738c] line-clamp-2 mb-3">
                      {rec.summary || rec.content}
                    </p>
                  </div>

                  <div>
                    <div className="flex flex-wrap gap-1 mb-2">
                      {rec.tags.slice(0, 3).map((tag, i) => (
                        <span key={i} className="inline-flex items-center gap-0.5 text-[9px] font-mono px-1.5 py-0.5 bg-[#faf8ff] text-[#73738c] rounded-md">
                          <Tag className="w-2.5 h-2.5" />
                          {tag}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center justify-between text-[10px] font-mono text-[#73738c] pt-2 border-t border-[#f4f4f5]">
                      <span>Agent: {rec.agent_role}</span>
                      <span className="flex items-center gap-1 group-hover:translate-x-0.5 transition-transform text-[#4648d4] font-semibold">
                        Inspect
                        <ChevronRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Retrieval Telemetry Log */}
      {activeTab === 'retrievals' && (
        <div className="space-y-3">
          {retrievalEvents.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-white border border-[#eaebf0] space-y-2">
              <Brain className="w-8 h-8 text-[#73738c] mx-auto opacity-50" />
              <h3 className="font-display font-bold text-sm text-[#131b2e]">0 retrieval events logged</h3>
              <p className="text-xs text-[#73738c] font-mono">
                No recent agent memory context queries have been executed yet. Trigger deliberation to view events.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {retrievalEvents.map((evt, idx) => (
                <div
                  key={evt.event_id || idx}
                  className="p-3.5 rounded-xl bg-white border border-[#eaebf0] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#ecfdf5] text-[#006c49] flex items-center justify-center shrink-0 font-bold">
                      <Brain className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-[#131b2e]">{evt.agent_role}</span>
                        <span className="px-1.5 py-0.5 bg-[#f4f4f5] rounded-md text-[10px] text-[#71717a]">
                          {evt.station_id.toUpperCase()}
                        </span>
                        <span className="text-[10px] text-[#73738c]">
                          {evt.timestamp_utc || 'Recently'}
                        </span>
                      </div>
                      <p className="text-[#464554]">
                        Query: <span className="text-[#131b2e] font-semibold">"{evt.query}"</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                    <span className="px-2 py-1 rounded-md bg-[#faf8ff] border border-[#eaedff] text-[#4648d4] font-bold">
                      {evt.memories_found} memories found
                    </span>
                    <span className="text-[#73738c]">
                      {evt.retrieval_latency_ms.toFixed(1)} ms
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      evt.memory_injection_success ? 'bg-[#ecfdf5] text-[#006c49]' : 'bg-[#fff1f2] text-[#e11d48]'
                    }`}>
                      {evt.memory_injection_success ? 'INJECTED_TO_LLM' : 'INJECTION_FAILED'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Memory Detail Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 shadow-2xl border border-[#eaebf0] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md bg-[#faf8ff] text-[#4648d4] font-mono text-xs font-bold border border-[#eaedff]">
                  {selectedRecord.memory_type}
                </span>
                <span className="font-mono text-xs text-[#73738c]">{selectedRecord.memory_id}</span>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="w-8 h-8 rounded-full hover:bg-[#f4f4f5] flex items-center justify-center text-[#73738c] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <h3 className="font-display font-black text-lg text-[#131b2e] mb-1">
                {selectedRecord.title}
              </h3>
              <p className="text-xs text-[#73738c] font-mono">
                Source: {selectedRecord.source} • Partition: {selectedRecord.agent_role} @ {selectedRecord.station_id.toUpperCase()}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff] text-xs font-mono text-[#464554] space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#73738c]">Operational Summary</span>
              <p>{selectedRecord.summary}</p>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#73738c]">Context Payload / SOP Action Text</span>
              <div className="p-4 rounded-xl bg-[#131b2e] text-[#a7f3d0] font-mono text-xs whitespace-pre-wrap leading-relaxed">
                {selectedRecord.content}
              </div>
            </div>

            {selectedRecord.tags && selectedRecord.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {selectedRecord.tags.map((tag, idx) => (
                  <span key={idx} className="px-2 py-0.5 bg-[#f4f4f5] text-[#464554] text-xs rounded-md font-mono">
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs font-mono text-[#73738c]">
              <span>Created: {new Date(selectedRecord.created_at_utc).toLocaleString()}</span>
              <span>Importance: {selectedRecord.importance.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Create Memory Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <form onSubmit={handleCreateSubmit} className="bg-white rounded-3xl max-w-xl w-full p-6 shadow-2xl border border-[#eaebf0] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-[#4648d4]" />
                <h3 className="font-display font-bold text-base text-[#131b2e]">Store Persistent Cognitive Memory</h3>
              </div>
              <button
                type="button"
                onClick={() => setCreateModalOpen(false)}
                className="w-8 h-8 rounded-full hover:bg-[#f4f4f5] flex items-center justify-center text-[#73738c] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div>
                <label className="block text-[#73738c] mb-1">Memory Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Contingency: Backup Genset Automatic Transfer Sequence"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#eaebf0] bg-[#faf8ff] text-[#131b2e] focus:outline-hidden focus:border-[#4648d4]"
                />
              </div>

              <div>
                <label className="block text-[#73738c] mb-1">Brief Summary</label>
                <input
                  type="text"
                  placeholder="Short one-line operational summary"
                  value={newSummary}
                  onChange={(e) => setNewSummary(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#eaebf0] bg-[#faf8ff] text-[#131b2e] focus:outline-hidden focus:border-[#4648d4]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[#73738c] mb-1">Memory Type</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value as MemoryType)}
                    className="w-full px-3 py-2 rounded-xl border border-[#eaebf0] bg-[#faf8ff] text-[#131b2e]"
                  >
                    <option value="SOP">SOP (Standard Operating Proc)</option>
                    <option value="INCIDENT">Incident Memory</option>
                    <option value="AGENT">Agent Knowledge</option>
                    <option value="STATION">Station Memory</option>
                    <option value="GLOBAL">Global Policy</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[#73738c] mb-1">Target Agent</label>
                  <select
                    value={newAgent}
                    onChange={(e) => setNewAgent(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#eaebf0] bg-[#faf8ff] text-[#131b2e]"
                  >
                    <option value="PLANNING">Planning Agent</option>
                    <option value="DIAGNOSTIC">Diagnostic Agent</option>
                    <option value="SITUATION_AWARENESS">Situation Awareness</option>
                    <option value="LIFE_SUPPORT">Life Support Agent</option>
                    <option value="ENERGY">Energy & Microgrid</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[#73738c] mb-1">Detailed Content (Injected into Agent Prompt)</label>
                <textarea
                  required
                  rows={4}
                  placeholder="Specify operational steps, physical constraints, and recovery thresholds..."
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#eaebf0] bg-[#faf8ff] text-[#131b2e] focus:outline-hidden focus:border-[#4648d4]"
                />
              </div>

              <div>
                <label className="block text-[#73738c] mb-1">Tags (Comma-separated)</label>
                <input
                  type="text"
                  value={newTags}
                  onChange={(e) => setNewTags(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#eaebf0] bg-[#faf8ff] text-[#131b2e]"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#eaebf0]">
              <button
                type="button"
                onClick={() => setCreateModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-[#eaebf0] text-xs font-mono font-semibold text-[#73738c] hover:bg-[#f4f4f5] cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating}
                className="px-4 py-2 rounded-xl bg-[#4648d4] text-white text-xs font-mono font-bold hover:bg-[#3b3dbf] cursor-pointer flex items-center gap-1.5"
              >
                {creating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Database className="w-3.5 h-3.5" />}
                <span>Persist Record</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
