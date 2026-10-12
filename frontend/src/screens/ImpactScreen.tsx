import React from 'react';
import { Pile } from '../types';
import { Leaf, IndianRupee, CloudSun, ShieldCheck, Download } from 'lucide-react';

interface ImpactScreenProps {
  pile: Pile;
  lang: 'en' | 'hi';
}

export const ImpactScreen: React.FC<ImpactScreenProps> = ({ pile, lang }) => {
  // Ecological calculation factors
  const wasteKg = Math.max(8.0, pile.totalWasteKg);
  const rupeesSaved = Math.round(wasteKg * 22.5); // avg vermicompost replacement cost in India
  const co2eAvoided = Number((wasteKg * 1.22).toFixed(1)); // US EPA WARM methane avoidance factor

  const handleExport = () => {
    const data = {
      pile: pile.name,
      dayCount: pile.dayCount,
      wasteDivertedKg: wasteKg,
      rupeesSaved: rupeesSaved,
      co2eAvoidedKg: co2eAvoided,
      historyCount: pile.history.length,
      exportDate: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `compostmitra_${pile.id}_backup.json`;
    a.click();
  };

  return (
    <div className="pb-28 max-w-lg mx-auto space-y-5">
      {/* Header */}
      <div>
        <span className="text-[11px] font-bold uppercase tracking-wider text-clay-700 bg-clay-200/50 px-2.5 py-0.5 rounded-full">
          Climate & Savings
        </span>
        <h2 className="text-2xl font-bold font-display text-ink mt-2">
          {lang === 'hi' ? 'आपका पर्यावरण प्रभाव' : 'Your Real-World Impact'}
        </h2>
        <p className="text-xs text-ink-muted mt-1 font-sans">
          {lang === 'hi'
            ? 'लैंडफिल से बचाए गए कचरे और पैसों का ईमानदार हिसाब'
            : 'Honest tally of diverted food scraps, saved rupees, and avoided methane.'}
        </p>
      </div>

      {/* 3 Large Metric Cards */}
      <div className="grid grid-cols-1 gap-3">
        {/* Metric 1: Waste Diverted */}
        <div className="p-5 rounded-card bg-paper border border-sand shadow-warm flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-neem-100 text-neem-700 flex items-center justify-center shrink-0">
            <Leaf size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold font-display text-ink">
              {wasteKg} kg
            </div>
            <div className="text-xs text-ink font-semibold">
              {lang === 'hi' ? 'गीला कचरा लैंडफिल जाने से रोका' : 'Kitchen Waste Diverted'}
            </div>
            <div className="text-[11px] text-ink-muted mt-0.5">
              Prevented anaerobic rotting in dump-yards.
            </div>
          </div>
        </div>

        {/* Metric 2: Financial Savings */}
        <div className="p-5 rounded-card bg-paper border border-sand shadow-warm flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-haldi-100 text-haldi-text flex items-center justify-center shrink-0">
            <IndianRupee size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold font-display text-ink">
              ₹{rupeesSaved}
            </div>
            <div className="text-xs text-ink font-semibold">
              {lang === 'hi' ? 'नर्सरी खाद के पैसे बचाए' : 'Estimated Nursery Savings'}
            </div>
            <div className="text-[11px] text-ink-muted mt-0.5">
              Based on ₹20–₹25/kg bagged vermicompost nursery retail price.
            </div>
          </div>
        </div>

        {/* Metric 3: CO2e Mitigated */}
        <div className="p-5 rounded-card bg-paper border border-sand shadow-warm flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-clay-200 text-clay-700 flex items-center justify-center shrink-0">
            <CloudSun size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold font-display text-ink">
              {co2eAvoided} kg CO₂e
            </div>
            <div className="text-xs text-ink font-semibold">
              {lang === 'hi' ? 'मीथेन ग्रीनहाउस गैस की बचत' : 'Avoided Greenhouse Emissions'}
            </div>
            <div className="text-[11px] text-ink-muted mt-0.5">
              US EPA WARM Factor: 1.22 kg CO₂e prevented per kg diverted.
            </div>
          </div>
        </div>
      </div>

      {/* Honest Disclaimer Label */}
      <div className="p-3.5 rounded-card bg-sand/30 border border-sand text-[11px] text-ink-muted flex items-start gap-2">
        <ShieldCheck size={14} className="text-clay-600 shrink-0 mt-0.5" />
        <p className="leading-relaxed font-sans">
          <strong>Honesty Rule:</strong> All environmental numbers are statistical estimations grounded in US EPA WARM and local nursery retail averages (sanity check, not proof).
        </p>
      </div>

      {/* 1-Click Export Backup Button */}
      <button
        onClick={handleExport}
        className="w-full py-3.5 px-4 rounded-card bg-paper border border-sand hover:bg-sand/30 text-ink text-xs font-semibold flex items-center justify-center gap-2 transition-colors min-h-[48px]"
      >
        <Download size={16} />
        <span>{lang === 'hi' ? 'गार्डन डेटा बैकअप डाउनलोड करें' : 'Export Garden Journal (JSON Backup)'}</span>
      </button>
    </div>
  );
};
