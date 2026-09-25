import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Zap, 
  Building, 
  CloudSnow, 
  Truck, 
  Search, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  Radio
} from 'lucide-react';
import { StationId } from '../../types';
import { fetchPillarTelemetry } from '../../api';

interface DigitalTwinViewProps {
  activeStation: StationId;
}

export const DigitalTwinView: React.FC<DigitalTwinViewProps> = ({ activeStation }) => {
  const [activePillar, setActivePillar] = useState<'energy' | 'infrastructure' | 'environment' | 'logistics'>('energy');
  const [sensors, setSensors] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadPillar = async () => {
    try {
      const data = await fetchPillarTelemetry(activeStation, activePillar);
      if (data?.readings) {
        setSensors(data.readings);
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    loadPillar();
    const interval = setInterval(loadPillar, 2500);
    return () => clearInterval(interval);
  }, [activeStation, activePillar]);

  const pillars = [
    { id: 'energy', label: 'Energy Pillar', count: '68 Sensors', icon: Zap },
    { id: 'infrastructure', label: 'Infrastructure Pillar', count: '192 Sensors', icon: Building },
    { id: 'environment', label: 'Environment Pillar', count: '128 Sensors', icon: CloudSnow },
    { id: 'logistics', label: 'Logistics Pillar', count: '117 Sensors', icon: Truck },
  ] as const;

  const sensorKeys = Object.keys(sensors);
  const filteredKeys = sensorKeys.filter((key) => {
    const s = sensors[key];
    const q = searchQuery.toLowerCase();
    return (
      key.toLowerCase().includes(q) ||
      (s.parameter && String(s.parameter).toLowerCase().includes(q)) ||
      (s.category && String(s.category).toLowerCase().includes(q)) ||
      (s.sensor_type && String(s.sensor_type).toLowerCase().includes(q))
    );
  });

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-[#eaebf0]">
        <div>
          <h1 className="font-display font-black text-2xl sm:text-3xl text-[#131b2e] tracking-tight">
            Physical Sensor Synoptic Grid
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-[#73738c] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search 505 sensors..."
              className="h-10 pl-9 pr-3 rounded-xl bg-white border border-[#eaebf0] text-xs text-[#131b2e] placeholder:text-[#73738c] focus:outline-hidden focus:border-[#4648d4] focus:ring-1 focus:ring-[#4648d4] shadow-2xs w-48 sm:w-64"
            />
          </div>

          <button
            onClick={loadPillar}
            className="p-2.5 rounded-xl bg-white border border-[#eaebf0] hover:bg-[#f2f3ff] text-[#464554] transition-colors shadow-2xs"
            title="Refresh Telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Pillar Switcher Tabs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {pillars.map((p) => {
          const Icon = p.icon;
          const isActive = activePillar === p.id;
          return (
            <button
              key={p.id}
              onClick={() => setActivePillar(p.id)}
              className={`p-4 rounded-2xl border text-left transition-all flex items-center justify-between ${
                isActive
                  ? 'bg-white border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-md'
                  : 'bg-white/80 hover:bg-white border-[#eaebf0] hover:border-[#c7c4d7]'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                    isActive ? 'bg-[#4648d4] text-white shadow-xs' : 'bg-[#f2f3ff] text-[#4648d4]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className={`text-sm font-bold ${isActive ? 'text-[#4648d4]' : 'text-[#131b2e]'}`}>
                    {p.label}
                  </div>
                  <div className="text-[11px] font-mono text-[#73738c]">{p.count}</div>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Sensor Channel Telemetry Grid */}
      <div className="rounded-2xl bg-white border border-[#eaebf0] p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#eaebf0]">
          <div className="flex items-center gap-2 text-xs font-mono text-[#73738c]">
            <Radio className="w-4 h-4 text-[#006577]" />
            <span>Showing {filteredKeys.length} of {sensorKeys.length} Channels</span>
          </div>
          <span className="text-[11px] font-mono font-semibold text-[#006c49] bg-[#ecfdf5] px-2.5 py-1 rounded-full">
            ● 100% Modbus TCP Sync
          </span>
        </div>

        {filteredKeys.length === 0 ? (
          <div className="py-12 text-center text-sm text-[#73738c]">
            No telemetry channels match &quot;{searchQuery}&quot;
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 max-h-[680px] overflow-y-auto pr-1">
            {filteredKeys.map((key) => {
              const item = sensors[key];
              const isGood = item.quality === 'GOOD';
              const displayVal = typeof item.value === 'number' 
                ? Number.isInteger(item.value) ? item.value : item.value.toFixed(2)
                : String(item.value);

              return (
                <div
                  key={key}
                  className="p-3.5 rounded-xl bg-[#faf8ff] border border-[#eaedff] flex flex-col justify-between hover:bg-white hover:border-[#c7c4d7] transition-all"
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="font-mono text-[10px] text-[#73738c] line-clamp-1" title={key}>
                      {key}
                    </span>
                    <span
                      className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm ${
                        isGood ? 'bg-[#ecfdf5] text-[#006c49]' : 'bg-[#fff1f2] text-[#e11d48]'
                      }`}
                    >
                      {item.quality || 'GOOD'}
                    </span>
                  </div>

                  <div className="flex items-baseline justify-between mt-1">
                    <span className="font-mono font-bold text-lg text-[#131b2e]">
                      {displayVal}
                    </span>
                    <span className="text-xs font-mono text-[#4648d4] font-semibold">
                      {item.unit || ''}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-[#73738c] mt-2 pt-2 border-t border-[#eaebf0]/60">
                    <span className="capitalize">{item.parameter?.replace(/_/g, ' ') || 'Telemetry'}</span>
                    <span className="font-mono text-[9px] uppercase text-[#006577]">{item.sensor_type || 'SENSOR'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
