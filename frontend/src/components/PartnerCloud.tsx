import React from 'react';

export const PartnerCloud: React.FC = () => {
  const partners = [
    { name: 'NCPOR Goa', role: 'Polar Research Centre' },
    { name: 'MoES Govt of India', role: 'Ministry of Earth Sciences' },
    { name: 'Survey of India', role: 'Geodetic Mapping' },
    { name: 'IMD Meteorology', role: 'Polar Weather Network' },
    { name: 'ISRO Telemetry', role: 'Satellite Ground Stations' },
  ];

  return (
    <section className="w-full bg-[#f2f3ff]/60 border-y border-[#eaebf0] py-10 mt-14">
      <div className="max-w-[1440px] mx-auto px-6">
        <h3 className="text-xs uppercase tracking-widest text-[#73738c] text-center mb-6 font-bold">
          Key Institutional Partners
        </h3>
        <div className="flex flex-wrap items-center justify-center gap-8 md:gap-14 opacity-90">
          {partners.map(p => (
            <span
              key={p.name}
              className="font-display font-bold text-base text-[#131b2e] tracking-tight hover:text-[#4648d4] transition-colors"
            >
              {p.name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
};
