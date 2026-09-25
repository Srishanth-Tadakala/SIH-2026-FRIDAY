import React from 'react';
import { 
  Compass, 
  Zap, 
  Thermometer, 
  Wind, 
  Fuel, 
  Droplet, 
  CheckCircle2, 
  Radio, 
  ArrowRight,
  ShieldAlert
} from 'lucide-react';
import { StationId, StationInfo } from '../types';

interface StationCardsSectionProps {
  activeStation: StationId;
  onStationChange: (station: StationId) => void;
  stationsData?: StationInfo[] | null;
}

export const StationCardsSection: React.FC<StationCardsSectionProps> = ({
  activeStation,
  onStationChange,
  stationsData,
}) => {
  const bharatiData = stationsData?.find((s) => s.station_id === 'bharati');
  const maitriData = stationsData?.find((s) => s.station_id === 'maitri');

  return (
    <section id="stations" className="w-full mb-10">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2 mb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold uppercase tracking-wider text-[#4648d4] mb-1">
            <Compass className="w-3.5 h-3.5" />
            <span>Dual Outpost Architecture</span>
          </div>
          <h2 className="font-display font-bold text-2xl text-[#131b2e] tracking-tight">
            Indian Antarctic Research Stations
          </h2>
          <p className="text-xs sm:text-sm text-[#464554] mt-0.5">
            Click any station card below to dynamically switch the live digital twin telemetry context.
          </p>
        </div>

        <div className="text-xs text-[#73738c] font-mono">
          <span>Active Context: </span>
          <span className="font-bold text-[#4648d4] uppercase">
            {activeStation === 'bharati' ? 'Bharati (69°S)' : 'Maitri (70°S)'}
          </span>
        </div>
      </div>

      {/* 2 Interactive Station Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* ================= CARD 1: BHARATI ================= */}
        <div
          onClick={() => onStationChange('bharati')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') onStationChange('bharati');
          }}
          className={`relative rounded-2xl p-6 transition-all duration-200 cursor-pointer text-left border ${
            activeStation === 'bharati'
              ? 'bg-white border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-lg shadow-[#4648d4]/10'
              : 'bg-white/80 hover:bg-white border-[#eaebf0] hover:border-[#c7c4d7] shadow-sm hover:shadow-md'
          }`}
        >
          {/* Active Context Glow Pill */}
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-[#4648d4]/10 text-[#4648d4] flex items-center justify-center font-bold font-mono text-sm border border-[#4648d4]/20">
                BH
              </div>
              <div>
                <h3 className="font-display font-bold text-lg text-[#131b2e] leading-tight">
                  Bharati Research Station
                </h3>
                <span className="text-xs text-[#73738c] font-medium">
                  Larsemann Hills, East Antarctica (69° 24&apos; S, 76° 11&apos; E)
                </span>
              </div>
            </div>

            {/* Active Status Badge */}
            {activeStation === 'bharati' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
                ACTIVE TWIN
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#f2f3ff] text-[#4648d4] text-xs font-medium">
                Click to Inspect
              </span>
            )}
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4">
            {/* Microgrid Load */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Zap className="w-3.5 h-3.5 text-[#4648d4]" />
                <span>Microgrid Load</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.station_electrical_load_kw?.toFixed(1) || '148.2'} kW
              </div>
              <span className="text-[10px] text-[#006c49] font-medium">50.00 Hz Nominal</span>
            </div>

            {/* Indoor Temperature */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Thermometer className="w-3.5 h-3.5 text-[#10b981]" />
                <span>Habitat Temp</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                +{bharatiData?.kpis?.indoor_avg_temp_c?.toFixed(1) || '20.2'}°C
              </div>
              <span className="text-[10px] text-[#006c49] font-medium">Safe Margin</span>
            </div>

            {/* Ambient Climate */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Wind className="w-3.5 h-3.5 text-[#006577]" />
                <span>Polar Wind</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.wind_speed_mps?.toFixed(1) || '12.0'} m/s
              </div>
              <span className="text-[10px] text-[#464554]">
                Ambient {bharatiData?.kpis?.ambient_temp_c?.toFixed(0) || '-18'}°C
              </span>
            </div>

            {/* Bulk Fuel Autonomy */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Fuel className="w-3.5 h-3.5 text-[#f59e0b]" />
                <span>Fuel Autonomy</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.fuel_autonomy_days?.toFixed(0) || '261'} Days
              </div>
              <span className="text-[10px] text-[#464554]">275,847 L Bulk</span>
            </div>

            {/* Potable Water Tank */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Droplet className="w-3.5 h-3.5 text-[#06b6d4]" />
                <span>Water Storage</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.potable_tank_level_pct?.toFixed(0) || '82'}% Level
              </div>
              <span className="text-[10px] text-[#006c49] font-medium">Trace Heat Active</span>
            </div>

            {/* Sensor Channels */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Radio className="w-3.5 h-3.5 text-[#4648d4]" />
                <span>Physics Sensors</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.sensor_count || 505} Points
              </div>
              <span className="text-[10px] text-[#006c49] font-medium">100% Online</span>
            </div>
          </div>

          {/* Action Row */}
          <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs">
            <span className="text-[#73738c]">
              Aerodynamic Stilt Architecture • Commissioned 2012
            </span>
            <div className="flex items-center gap-1 font-semibold text-[#4648d4]">
              {activeStation === 'bharati' ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-[#006c49]" />
                  <span>Currently Active Twin</span>
                </>
              ) : (
                <>
                  <span>Select Bharati</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </div>
          </div>
        </div>

        {/* ================= CARD 2: MAITRI ================= */}
        <div
          onClick={() => onStationChange('maitri')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') onStationChange('maitri');
          }}
          className={`relative rounded-2xl p-6 transition-all duration-200 cursor-pointer text-left border ${
            activeStation === 'maitri'
              ? 'bg-white border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-lg shadow-[#4648d4]/10'
              : 'bg-white/80 hover:bg-white border-[#eaebf0] hover:border-[#c7c4d7] shadow-sm hover:shadow-md'
          }`}
        >
          {/* Active Context Glow Pill */}
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-[#006577]/10 text-[#006577] flex items-center justify-center font-bold font-mono text-sm border border-[#006577]/20">
                MT
              </div>
              <div>
                <h3 className="font-display font-bold text-lg text-[#131b2e] leading-tight">
                  Maitri Research Station
                </h3>
                <span className="text-xs text-[#73738c] font-medium">
                  Schirmacher Oasis, Queen Maud Land (70° 45&apos; S, 11° 43&apos; E)
                </span>
              </div>
            </div>

            {/* Active Status Badge */}
            {activeStation === 'maitri' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
                ACTIVE TWIN
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#f2f3ff] text-[#4648d4] text-xs font-medium">
                Click to Inspect
              </span>
            )}
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4">
            {/* Microgrid Load */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Zap className="w-3.5 h-3.5 text-[#4648d4]" />
                <span>Microgrid Load</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.station_electrical_load_kw?.toFixed(1) || '148.0'} kW
              </div>
              <span className="text-[10px] text-[#006c49] font-medium">50.00 Hz Nominal</span>
            </div>

            {/* Indoor Temperature */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Thermometer className="w-3.5 h-3.5 text-[#10b981]" />
                <span>Habitat Temp</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                +{maitriData?.kpis?.indoor_avg_temp_c?.toFixed(1) || '20.2'}°C
              </div>
              <span className="text-[10px] text-[#006c49] font-medium">Safe Margin</span>
            </div>

            {/* Ambient Climate */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Wind className="w-3.5 h-3.5 text-[#006577]" />
                <span>Polar Wind</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.wind_speed_mps?.toFixed(1) || '12.0'} m/s
              </div>
              <span className="text-[10px] text-[#464554]">
                Ambient {maitriData?.kpis?.ambient_temp_c?.toFixed(0) || '-18'}°C
              </span>
            </div>

            {/* Bulk Fuel Autonomy */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Fuel className="w-3.5 h-3.5 text-[#f59e0b]" />
                <span>Fuel Autonomy</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.fuel_autonomy_days?.toFixed(0) || '262'} Days
              </div>
              <span className="text-[10px] text-[#464554]">275,850 L Bulk</span>
            </div>

            {/* Potable Water Tank */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Droplet className="w-3.5 h-3.5 text-[#06b6d4]" />
                <span>Water Storage</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.potable_tank_level_pct?.toFixed(0) || '82'}% Level
              </div>
              <span className="text-[10px] text-[#006c49] font-medium">Priyadarshini Lake</span>
            </div>

            {/* Sensor Channels */}
            <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Radio className="w-3.5 h-3.5 text-[#4648d4]" />
                <span>Physics Sensors</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.sensor_count || 505} Points
              </div>
              <span className="text-[10px] text-[#006c49] font-medium">100% Online</span>
            </div>
          </div>

          {/* Action Row */}
          <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs">
            <span className="text-[#73738c]">
              Inland Oasis Habitat • Commissioned 1989
            </span>
            <div className="flex items-center gap-1 font-semibold text-[#4648d4]">
              {activeStation === 'maitri' ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-[#006c49]" />
                  <span>Currently Active Twin</span>
                </>
              ) : (
                <>
                  <span>Select Maitri</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
