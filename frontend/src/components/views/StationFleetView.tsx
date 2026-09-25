import React, { useState, useEffect } from 'react';
import { 
  Compass, 
  Zap, 
  Thermometer, 
  Wind, 
  Fuel, 
  Droplet, 
  Truck, 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  Radio, 
  RefreshCw, 
  ArrowRight,
  Play
} from 'lucide-react';
import { StationId, StationInfo } from '../../types';
import { fetchStations, injectScenario, clearScenario } from '../../api';

interface StationFleetViewProps {
  activeStation: StationId;
  onStationChange: (station: StationId) => void;
}

export const StationFleetView: React.FC<StationFleetViewProps> = ({
  activeStation,
  onStationChange,
}) => {
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadFleet = async () => {
    try {
      const data = await fetchStations();
      setStations(data);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFleet();
    const interval = setInterval(loadFleet, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerScenario = async (targetStation: StationId, scenario: string) => {
    setActionMessage(`Triggering ${scenario} on ${targetStation.toUpperCase()}...`);
    try {
      await injectScenario(scenario, { station_id: targetStation });
      setActionMessage(`Scenario ${scenario} active on ${targetStation.toUpperCase()}`);
      await loadFleet();
    } catch {
      setActionMessage(`Failed to inject scenario.`);
    }
    setTimeout(() => setActionMessage(null), 3500);
  };

  const handleResetStation = async (targetStation: StationId) => {
    setActionMessage(`Restoring nominal baseline for ${targetStation.toUpperCase()}...`);
    try {
      await clearScenario(targetStation);
      setActionMessage(`Station ${targetStation.toUpperCase()} nominal.`);
      await loadFleet();
    } catch {
      setActionMessage(`Reset failed.`);
    }
    setTimeout(() => setActionMessage(null), 3500);
  };

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-[#eaebf0]">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-mono font-bold uppercase tracking-wider text-[#4648d4] mb-1">
            <Compass className="w-3.5 h-3.5" />
            <span>DTIARS FLEET MANAGEMENT CONSOLE</span>
          </div>
          <h1 className="font-display font-black text-2xl sm:text-3xl text-[#131b2e] tracking-tight">
            Indian Antarctic Research Station Fleet
          </h1>
          <p className="text-xs sm:text-sm text-[#464554] mt-0.5">
            Real-time synchronization across Bharati (Larsemann Hills) and Maitri (Schirmacher Oasis).
          </p>
        </div>

        <div className="flex items-center gap-2">
          {actionMessage && (
            <span className="text-xs font-mono text-[#4648d4] bg-[#eaedff] px-3 py-1 rounded-full animate-fade-in">
              {actionMessage}
            </span>
          )}
          <button
            onClick={loadFleet}
            className="p-2 rounded-xl bg-white border border-[#eaebf0] hover:bg-[#f2f3ff] text-[#464554] transition-colors shadow-2xs"
            title="Refresh Fleet Telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Fleet Stations Comparison Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {stations.map((st) => {
          const isSelected = activeStation === st.station_id;
          const kpis = st.kpis;
          return (
            <div
              key={st.station_id}
              className={`rounded-2xl p-6 bg-white border transition-all duration-200 text-left ${
                isSelected
                  ? 'border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-lg shadow-[#4648d4]/10'
                  : 'border-[#eaebf0] hover:border-[#c7c4d7] shadow-sm'
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#4648d4]/10 text-[#4648d4] flex items-center justify-center font-mono font-bold text-sm border border-[#4648d4]/20">
                    {st.station_id === 'bharati' ? 'BH' : 'MT'}
                  </div>
                  <div>
                    <h2 className="font-display font-bold text-xl text-[#131b2e] leading-tight">
                      {st.station_name}
                    </h2>
                    <span className="text-xs text-[#73738c] font-medium">
                      {st.location} ({st.coordinates.latitude_dms}, {st.coordinates.longitude_dms})
                    </span>
                  </div>
                </div>

                {isSelected ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] text-xs font-semibold">
                    <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
                    ACTIVE CONTEXT
                  </span>
                ) : (
                  <button
                    onClick={() => onStationChange(st.station_id)}
                    className="px-3 py-1 rounded-full bg-[#f2f3ff] hover:bg-[#eaedff] text-[#4648d4] text-xs font-semibold transition-colors"
                  >
                    Select Context
                  </button>
                )}
              </div>

              {/* Status Pills Strip */}
              <div className="flex flex-wrap items-center gap-2 mb-4 text-xs font-mono">
                <span className="px-2.5 py-1 rounded-md bg-[#faf8ff] border border-[#eaedff] text-[#4648d4]">
                  Scenario: {st.active_scenario || 'NORMAL'}
                </span>
                <span className="px-2.5 py-1 rounded-md bg-[#faf8ff] border border-[#eaedff] text-[#006c49]">
                  {st.sensor_count} Sensors 100% Online
                </span>
                <span className="px-2.5 py-1 rounded-md bg-[#faf8ff] border border-[#eaedff] text-[#006577]">
                  Elevation: {st.coordinates.elevation_m}m ASL
                </span>
              </div>

              {/* Comprehensive KPI Metric Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4">
                {/* Generation vs Load */}
                <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
                  <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                    <Zap className="w-3.5 h-3.5 text-[#4648d4]" />
                    <span>Microgrid Load</span>
                  </div>
                  <div className="font-mono font-bold text-base text-[#131b2e]">
                    {kpis?.station_electrical_load_kw?.toFixed(1) || '148.0'} kW
                  </div>
                  <span className="text-[10px] text-[#006c49] font-medium">
                    Gen: {kpis?.total_generation_kw?.toFixed(1) || '148.4'} kW
                  </span>
                </div>

                {/* Thermal Heating */}
                <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
                  <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                    <Thermometer className="w-3.5 h-3.5 text-[#10b981]" />
                    <span>Habitat Temp</span>
                  </div>
                  <div className="font-mono font-bold text-base text-[#131b2e]">
                    +{kpis?.indoor_avg_temp_c?.toFixed(1) || '20.2'}°C
                  </div>
                  <span className="text-[10px] text-[#464554]">
                    Demand: {kpis?.station_heating_demand_kw?.toFixed(0) || '112'} kWth
                  </span>
                </div>

                {/* Polar Climate */}
                <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
                  <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                    <Wind className="w-3.5 h-3.5 text-[#006577]" />
                    <span>Polar Wind</span>
                  </div>
                  <div className="font-mono font-bold text-base text-[#131b2e]">
                    {kpis?.wind_speed_mps?.toFixed(1) || '12.0'} m/s
                  </div>
                  <span className="text-[10px] text-[#464554]">
                    Ext: {kpis?.ambient_temp_c?.toFixed(0) || '-18'}°C
                  </span>
                </div>

                {/* Fuel Autonomy */}
                <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
                  <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                    <Fuel className="w-3.5 h-3.5 text-[#f59e0b]" />
                    <span>Fuel Autonomy</span>
                  </div>
                  <div className="font-mono font-bold text-base text-[#131b2e]">
                    {kpis?.fuel_autonomy_days?.toFixed(0) || '261'} Days
                  </div>
                  <span className="text-[10px] text-[#464554]">
                    {kpis?.total_fuel_reserve_l ? (kpis.total_fuel_reserve_l / 1000).toFixed(0) + 'k L' : '275k L'}
                  </span>
                </div>

                {/* Water Storage */}
                <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
                  <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                    <Droplet className="w-3.5 h-3.5 text-[#06b6d4]" />
                    <span>Water Autonomy</span>
                  </div>
                  <div className="font-mono font-bold text-base text-[#131b2e]">
                    {kpis?.water_autonomy_days?.toFixed(1) || '7.5'} Days
                  </div>
                  <span className="text-[10px] text-[#006c49] font-medium">
                    {kpis?.potable_tank_level_pct?.toFixed(0) || '82'}% Reservoir
                  </span>
                </div>

                {/* Logistics Fleet */}
                <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
                  <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                    <Truck className="w-3.5 h-3.5 text-[#73738c]" />
                    <span>Fleet Ready</span>
                  </div>
                  <div className="font-mono font-bold text-base text-[#131b2e]">
                    {kpis?.fleet_availability_pct?.toFixed(1) || '93.8'}%
                  </div>
                  <span className="text-[10px] text-[#006c49] font-medium">
                    Route: {kpis?.ground_route_accessibility_pct?.toFixed(0) || '100'}%
                  </span>
                </div>
              </div>

              {/* Station Controls & Scenario Triggers */}
              <div className="pt-4 border-t border-[#eaebf0] flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTriggerScenario(st.station_id, 'GENERATOR_TRIP')}
                    className="px-3 py-1.5 rounded-lg bg-[#fff1f2] hover:bg-[#ffe4e6] text-[#e11d48] text-xs font-semibold transition-colors flex items-center gap-1.5"
                  >
                    <Play className="w-3 h-3" />
                    <span>Gen Trip</span>
                  </button>

                  <button
                    onClick={() => handleTriggerScenario(st.station_id, 'BLIZZARD_STRIKE')}
                    className="px-3 py-1.5 rounded-lg bg-[#f0f9ff] hover:bg-[#e0f2fe] text-[#0284c7] text-xs font-semibold transition-colors flex items-center gap-1.5"
                  >
                    <Play className="w-3 h-3" />
                    <span>Blizzard</span>
                  </button>

                  <button
                    onClick={() => handleResetStation(st.station_id)}
                    className="px-3 py-1.5 rounded-lg bg-[#f2f3ff] hover:bg-[#eaedff] text-[#4648d4] text-xs font-semibold transition-colors"
                  >
                    Reset
                  </button>
                </div>

                {!isSelected && (
                  <button
                    onClick={() => onStationChange(st.station_id)}
                    className="text-xs font-semibold text-[#4648d4] hover:underline flex items-center gap-1"
                  >
                    <span>Switch Active View</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
