import React from 'react';
import { Timer, Radio, HeartPulse } from 'lucide-react';

export const MetricRoiCards: React.FC = () => {
  return (
    <section id="metrics" className="w-full bg-[#f2f3ff] py-16 border-y border-[#eaebf0]">
      <div className="max-w-[1440px] mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Stat Card 1 */}
          <div className="p-8 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
            <div className="w-12 h-12 rounded-xl bg-[#6cf8bb]/30 text-[#006c49] flex items-center justify-center mb-6">
              <Timer className="w-6 h-6" />
            </div>
            <div>
              <span className="font-display font-extrabold text-4xl sm:text-5xl text-[#006c49] tracking-tight">
                1.2 sec
              </span>
              <h4 className="font-display font-bold text-base text-[#131b2e] mt-2">
                Autonomous Incident Resolution
              </h4>
            </div>
          </div>

          {/* Stat Card 2 */}
          <div className="p-8 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
            <div className="w-12 h-12 rounded-xl bg-[#acedff]/50 text-[#006577] flex items-center justify-center mb-6">
              <Radio className="w-6 h-6" />
            </div>
            <div>
              <span className="font-display font-extrabold text-4xl sm:text-5xl text-[#006577] tracking-tight">
                90%
              </span>
              <h4 className="font-display font-bold text-base text-[#131b2e] mt-2">
                Satcom Delta Compression
              </h4>
            </div>
          </div>

          {/* Stat Card 3 */}
          <div className="p-8 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
            <div className="w-12 h-12 rounded-xl bg-[#e1e0ff] text-[#4648d4] flex items-center justify-center mb-6">
              <HeartPulse className="w-6 h-6" />
            </div>
            <div>
              <span className="font-display font-extrabold text-4xl sm:text-5xl text-[#4648d4] tracking-tight">
                99.98%
              </span>
              <h4 className="font-display font-bold text-base text-[#131b2e] mt-2">
                Life-Support Envelope Retention
              </h4>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
