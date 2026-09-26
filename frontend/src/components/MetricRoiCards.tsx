import React from 'react';
import { Timer, Radio, HeartPulse } from 'lucide-react';

export const MetricRoiCards: React.FC = () => {
  return (
    <section id="metrics" className="w-full bg-[#faf8ff] py-12 border-y border-[#eaebf0]">
      <div className="max-w-[1440px] mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Stat Card 1 */}
          <div className="p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-xs flex items-center justify-between">
            <div>
              <span className="font-display font-black text-3xl sm:text-4xl text-[#006c49] tracking-tight font-mono">
                1.2s
              </span>
              <h4 className="font-display font-bold text-sm text-[#131b2e] mt-1">
                Autonomous Mitigation
              </h4>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-[#ecfdf5] text-[#006c49] flex items-center justify-center">
              <Timer className="w-6 h-6" />
            </div>
          </div>

          {/* Stat Card 2 */}
          <div className="p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-xs flex items-center justify-between">
            <div>
              <span className="font-display font-black text-3xl sm:text-4xl text-[#006577] tracking-tight font-mono">
                90%
              </span>
              <h4 className="font-display font-bold text-sm text-[#131b2e] mt-1">
                Satcom Delta Savings
              </h4>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-[#ecfeff] text-[#006577] flex items-center justify-center">
              <Radio className="w-6 h-6" />
            </div>
          </div>

          {/* Stat Card 3 */}
          <div className="p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-xs flex items-center justify-between">
            <div>
              <span className="font-display font-black text-3xl sm:text-4xl text-[#4648d4] tracking-tight font-mono">
                99.98%
              </span>
              <h4 className="font-display font-bold text-sm text-[#131b2e] mt-1">
                Life-Support Retention
              </h4>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-[#faf8ff] text-[#4648d4] flex items-center justify-center border border-[#eaedff]">
              <HeartPulse className="w-6 h-6" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
