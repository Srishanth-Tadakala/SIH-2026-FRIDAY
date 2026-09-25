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
        <p className="text-xs uppercase tracking-widest text-[#464554] text-center mb-8 font-semibold">
          Engineered for Indian Antarctic Research Stations • Under Ministry of Earth Sciences, Govt of India
        </p>
        <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16 opacity-80 hover:opacity-100 transition-opacity">
          {partners.map(p => (
            <div key={p.name} className="flex flex-col items-center">
              <span className="font-display font-bold text-lg text-[#131b2e] tracking-tight hover:text-[#4648d4] transition-colors">
                {p.name}
              </span>
              <span className="text-[10px] text-[#464554] font-medium mt-0.5">{p.role}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
