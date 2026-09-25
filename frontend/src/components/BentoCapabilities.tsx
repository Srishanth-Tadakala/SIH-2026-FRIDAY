import React from 'react';
import { Zap, Droplet, Brain, Shield, ArrowUpRight } from 'lucide-react';

export const BentoCapabilities: React.FC = () => {
  const capabilities = [
    {
      icon: <Zap className="w-6 h-6 text-[#006577]" />,
      badge: 'Zero Blackout Risk',
      badgeColor: 'bg-[#acedff]/50 text-[#001f26]',
      glowColor: 'bg-[#acedff]',
      title: 'Intelligent Microgrid Autonomy',
      description: 'Continuous 400V 50Hz frequency synchronization, automated standby diesel auto-transfer in 1.2s, and non-critical scientific load shedding.',
      linkText: 'Explore Microgrid SLD',
    },
    {
      icon: <Droplet className="w-6 h-6 text-[#006c49]" />,
      badge: 'Thermal Preservation',
      badgeColor: 'bg-[#6cf8bb]/40 text-[#002113]',
      glowColor: 'bg-[#6cf8bb]',
      title: 'Predictive Freeze Prevention',
      description: 'Physics-informed thermal decay lookahead algorithms. Auto-energizes utilidor potable water trace heating before pipe freeze-up at -40°C.',
      linkText: 'Inspect Utilidor Loops',
    },
    {
      icon: <Brain className="w-6 h-6 text-[#4648d4]" />,
      badge: 'Sub-400ms Groq LPU',
      badgeColor: 'bg-[#e1e0ff] text-[#07006c]',
      glowColor: 'bg-[#e1e0ff]',
      title: '10-Agent Cognitive Society',
      description: 'Perception, causal diagnostic, predictive forward forecasting, and What-If sandbox verification collaborating on a 35-node causal DAG with zero hallucination.',
      linkText: 'View Agent Society',
    },
    {
      icon: <Shield className="w-6 h-6 text-[#ba1a1a]" />,
      badge: 'Tiered Safety Interlocks',
      badgeColor: 'bg-[#ffdad6] text-[#93000a]',
      glowColor: 'bg-[#ffdad6]',
      title: 'Defense Safety Interlocks',
      description: 'Tier 1 sub-second autonomous urgency, Tier 2 supervised 60-second abort window, and Tier 3 cryptographic Commander PIN verification.',
      linkText: 'Review Interlock Specs',
    },
  ];

  return (
    <section id="capabilities" className="w-full max-w-[1440px] mx-auto px-6 py-16">
      <div className="text-center max-w-2xl mx-auto mb-10">
        <h2 className="font-display font-extrabold text-3xl sm:text-4xl text-[#131b2e] tracking-tight">
          Core Platform Capabilities
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {capabilities.map(cap => (
          <div
            key={cap.title}
            className="p-6 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between hover:shadow-md hover:border-[#4648d4]/30 transition-all relative overflow-hidden group"
          >
            <div className={`absolute -right-6 -bottom-6 w-28 h-28 ${cap.glowColor} rounded-full blur-2xl opacity-40 group-hover:opacity-80 transition-opacity`} />
            
            <div>
              <div className="w-12 h-12 rounded-xl bg-[#f2f3ff] flex items-center justify-center mb-6">
                {cap.icon}
              </div>
              <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${cap.badgeColor}`}>
                {cap.badge}
              </span>
              <h3 className="font-display font-bold text-base text-[#131b2e] mt-3 mb-2">
                {cap.title}
              </h3>
            </div>

            <div className="mt-6 pt-4 border-t border-[#eaebf0] flex items-center gap-1.5 text-xs font-semibold text-[#4648d4] group-hover:text-[#6063ee]">
              <span>{cap.linkText}</span>
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
