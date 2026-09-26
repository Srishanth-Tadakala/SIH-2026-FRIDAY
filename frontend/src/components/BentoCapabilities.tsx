import React from 'react';
import { Zap, Droplet, Brain, Shield, ArrowUpRight } from 'lucide-react';

export const BentoCapabilities: React.FC = () => {
  const capabilities = [
    {
      icon: <Zap className="w-5 h-5 text-[#4648d4]" />,
      badge: 'Grid Sync',
      badgeColor: 'bg-[#faf8ff] text-[#4648d4] border border-[#eaedff]',
      title: 'Microgrid Autonomy',
      linkText: 'Microgrid SLD',
    },
    {
      icon: <Droplet className="w-5 h-5 text-[#006577]" />,
      badge: 'Thermal Preservation',
      badgeColor: 'bg-[#ecfeff] text-[#0891b2] border border-[#a5f3fc]',
      title: 'Freeze Prevention',
      linkText: 'Utilidor Loops',
    },
    {
      icon: <Brain className="w-5 h-5 text-[#4648d4]" />,
      badge: '40ms Inference',
      badgeColor: 'bg-[#faf8ff] text-[#4648d4] border border-[#eaedff]',
      title: '10-Agent Society',
      linkText: 'Causal Reasoner',
    },
    {
      icon: <Shield className="w-5 h-5 text-[#006c49]" />,
      badge: 'Tier 1 Safeguards',
      badgeColor: 'bg-[#ecfdf5] text-[#006c49] border border-[#a7f3d0]',
      title: 'Defense Interlocks',
      linkText: 'Interlock Specs',
    },
  ];

  return (
    <section id="capabilities" className="w-full max-w-[1440px] mx-auto px-6 py-12">
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-display font-bold text-2xl text-[#131b2e] tracking-tight">
          Platform Capabilities
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {capabilities.map(cap => (
          <div
            key={cap.title}
            className="p-5 rounded-3xl bg-white border border-[#eaebf0] shadow-xs flex flex-col justify-between hover:shadow-md hover:border-[#4648d4]/30 transition-all group"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-2xl bg-[#faf8ff] border border-[#eaedff] flex items-center justify-center">
                  {cap.icon}
                </div>
                <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${cap.badgeColor}`}>
                  {cap.badge}
                </span>
              </div>
              <h3 className="font-display font-bold text-base text-[#131b2e]">
                {cap.title}
              </h3>
            </div>

            <div className="mt-5 pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs font-mono font-semibold text-[#4648d4] group-hover:text-[#3b3dbf]">
              <span>{cap.linkText}</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
