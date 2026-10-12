import React, { useState } from 'react';
import { PLANTS_DATA } from '../data/plants';
import { PlantProfile } from '../types';
import { Sun, ShieldAlert, Sparkles, Sprout, Heart } from 'lucide-react';

interface PlantsDosingScreenProps {
  lang: 'en' | 'hi';
}

export const PlantsDosingScreen: React.FC<PlantsDosingScreenProps> = ({ lang }) => {
  const [selectedPlant, setSelectedPlant] = useState<PlantProfile>(PLANTS_DATA[0]);
  const [vigor, setVigor] = useState<'thriving' | 'moderate' | 'struggling'>('thriving');

  return (
    <div className="pb-28 max-w-lg mx-auto space-y-5">
      {/* Header */}
      <div>
        <span className="text-[11px] font-bold uppercase tracking-wider text-clay-700 bg-clay-200/50 px-2.5 py-0.5 rounded-full">
          Honest Agronomy
        </span>
        <h2 className="text-2xl font-bold font-display text-ink mt-2">
          {lang === 'hi' ? 'पौधों को खाद देने का नियम' : 'Plant Dosing & Care Guide'}
        </h2>
        <p className="text-xs text-ink-muted mt-1 font-sans">
          {lang === 'hi'
            ? 'गमले के आकार और धूप के हिसाब से सटीक मुट्ठी खुराक'
            : 'Safe monthly handful dosages per pot size and sunlight band.'}
        </p>
      </div>

      {/* Plant Selector Horizontal Chips */}
      <div className="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1 no-scrollbar">
        {PLANTS_DATA.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setSelectedPlant(p)}
            className={`px-3.5 py-2 rounded-full text-xs font-semibold shrink-0 transition-all ${
              selectedPlant.id === p.id
                ? 'bg-clay-600 text-paper shadow-sm'
                : 'bg-paper border border-sand text-ink hover:bg-sand/40'
            }`}
          >
            {lang === 'hi' ? p.hinglishName : p.name}
          </button>
        ))}
      </div>

      {/* Selected Plant Dose Card */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm space-y-4">
        <div className="flex items-start justify-between border-b border-sand pb-3">
          <div>
            <h3 className="text-xl font-bold font-display text-ink">
              {lang === 'hi' ? selectedPlant.hinglishName : selectedPlant.name}
            </h3>
            <p className="text-xs text-ink-muted font-sans mt-0.5">
              {selectedPlant.family} · {selectedPlant.containerSize}
            </p>
          </div>
          <div className="text-right">
            <span className="text-xs font-bold text-neem-700 bg-neem-100 px-2.5 py-1 rounded-full">
              {selectedPlant.compostPerMonthHandfuls} mutthi / mo
            </span>
          </div>
        </div>

        {/* Sunlight & Pot Specs */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-card bg-cream border border-sand flex items-center gap-2.5">
            <Sun size={18} className="text-haldi-500 shrink-0" />
            <div>
              <div className="font-bold text-ink">{selectedPlant.sunlightHours} hrs Sun</div>
              <div className="text-[11px] text-ink-muted">Daily Direct Light</div>
            </div>
          </div>
          <div className="p-3 rounded-card bg-cream border border-sand flex items-center gap-2.5">
            <Sprout size={18} className="text-neem-700 shrink-0" />
            <div>
              <div className="font-bold text-ink">Top-dress</div>
              <div className="text-[11px] text-ink-muted">Every 30 Days</div>
            </div>
          </div>
        </div>

        {/* Application Stage Tip */}
        <div className="p-3.5 rounded-card bg-clay-200/40 border border-clay-200">
          <div className="text-[11px] font-bold text-clay-700 uppercase tracking-wider flex items-center gap-1.5 mb-1">
            <Sparkles size={13} />
            {lang === 'hi' ? 'प्रयोग करने की विधि:' : 'How to apply:'}
          </div>
          <p className="text-xs text-ink leading-relaxed font-sans">
            {selectedPlant.stageNote}
          </p>
        </div>

        {/* Hard Honesty Disclaimer */}
        <div className="p-3 rounded-card bg-sand/40 border border-sand text-[11px] text-ink-muted flex items-start gap-2">
          <ShieldAlert size={14} className="text-clay-600 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong>Mandatory Agronomic Fact:</strong> Compost is a living biological soil builder and organic supplement, not a chemical fertilizer replacement. Model estimates reflect statistical associations.
          </p>
        </div>
      </div>

      {/* 30-Second Plant Vigor Tracker */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm">
        <h4 className="text-xs font-bold uppercase tracking-wider text-ink-muted mb-2 flex items-center gap-1.5">
          <Heart size={14} className="text-clay-600" />
          {lang === 'hi' ? 'पौधे की सेहत (Vigor Check)' : 'Quick Plant Vigor Check'}
        </h4>
        <p className="text-xs text-ink-muted mb-3">
          {lang === 'hi'
            ? 'आपका पौधा इस समय कैसा महसूस कर रहा है?'
            : 'How is your plant looking today?'}
        </p>

        <div className="grid grid-cols-3 gap-2 text-xs">
          <button
            type="button"
            onClick={() => setVigor('thriving')}
            className={`py-2.5 px-2 rounded-card font-semibold text-center border transition-all ${
              vigor === 'thriving'
                ? 'bg-neem-100 border-neem-700 text-neem-700 ring-1 ring-neem-700'
                : 'bg-cream border-sand text-ink'
            }`}
          >
            🟢 Thriving
          </button>
          <button
            type="button"
            onClick={() => setVigor('moderate')}
            className={`py-2.5 px-2 rounded-card font-semibold text-center border transition-all ${
              vigor === 'moderate'
                ? 'bg-haldi-100 border-haldi-500 text-haldi-text ring-1 ring-haldi-500'
                : 'bg-cream border-sand text-ink'
            }`}
          >
            🟡 Moderate
          </button>
          <button
            type="button"
            onClick={() => setVigor('struggling')}
            className={`py-2.5 px-2 rounded-card font-semibold text-center border transition-all ${
              vigor === 'struggling'
                ? 'bg-clay-200 border-clay-600 text-clay-700 ring-1 ring-clay-600'
                : 'bg-cream border-sand text-ink'
            }`}
          >
            🔴 Struggling
          </button>
        </div>
      </div>
    </div>
  );
};
