import React from 'react';
import { DOCTOR_SYMPTOMS } from '../data/doctorRules';
import { DoctorSymptom } from '../types';
import { MatkaMitra } from '../components/MatkaMitra';
import { Wind, Bug, ThermometerSnowflake, Droplets, ArrowRight } from 'lucide-react';

interface BinDoctorScreenProps {
  onSelectSymptom: (symptom: DoctorSymptom) => void;
  lang: 'en' | 'hi';
}

export const BinDoctorScreen: React.FC<BinDoctorScreenProps> = ({
  onSelectSymptom,
  lang,
}) => {
  return (
    <div className="pb-24">
      {/* Calm Header */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm mb-5">
        <div className="flex items-center gap-3">
          <MatkaMitra tone="sniffing" size={48} />
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-clay-700 bg-clay-200/50 px-2 py-0.5 rounded-full">
              Bin Doctor Triage
            </span>
            <h2 className="text-xl font-bold font-display text-ink mt-1">
              {lang === 'hi'
                ? '"कोई बात नहीं। बताओ क्या हो रहा है?"'
                : '"Don\'t worry. Tell me what is happening."'}
            </h2>
          </div>
        </div>
        <p className="text-xs text-ink-muted mt-2 leading-relaxed">
          {lang === 'hi'
            ? 'कंपोस्ट में कभी-कभी बदबू या कीड़े आना बिल्कुल सामान्य है। 3 टैप में समाधान पाएं।'
            : 'Every compost pile hits a bump. Smell and bugs are completely normal. Pick what you notice below:'}
        </p>
      </div>

      {/* 2x2 Large Touch Category Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
        {/* Category 1: Smell */}
        <div className="p-4 rounded-card bg-paper border border-sand shadow-sm">
          <div className="flex items-center gap-2 mb-2 text-clay-700">
            <Wind size={18} />
            <h3 className="font-display font-bold text-base text-ink">
              {lang === 'hi' ? 'बदबू (Smell)' : 'Bad Smell'}
            </h3>
          </div>
          <p className="text-[11px] text-ink-muted mb-3 font-sans">
            Ammonia urine odor or rotten egg sewer stench.
          </p>
          <div className="space-y-2">
            {DOCTOR_SYMPTOMS.filter((s) => s.category === 'smell').map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => onSelectSymptom(s)}
                className="w-full text-left p-3 rounded-card bg-cream hover:bg-sand/60 border border-sand/80 text-xs font-semibold text-ink flex items-center justify-between transition-colors min-h-[48px]"
              >
                <span>{lang === 'hi' ? s.hinglishTitle : s.title}</span>
                <ArrowRight size={14} className="text-clay-600 shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* Category 2: Pests */}
        <div className="p-4 rounded-card bg-paper border border-sand shadow-sm">
          <div className="flex items-center gap-2 mb-2 text-clay-700">
            <Bug size={18} />
            <h3 className="font-display font-bold text-base text-ink">
              {lang === 'hi' ? 'कीड़े / मक्खियां (Pests)' : 'Insects & Flies'}
            </h3>
          </div>
          <p className="text-[11px] text-ink-muted mb-3 font-sans">
            Fruit flies hovering or larvae crawling.
          </p>
          <div className="space-y-2">
            {DOCTOR_SYMPTOMS.filter((s) => s.category === 'pests').map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => onSelectSymptom(s)}
                className="w-full text-left p-3 rounded-card bg-cream hover:bg-sand/60 border border-sand/80 text-xs font-semibold text-ink flex items-center justify-between transition-colors min-h-[48px]"
              >
                <span>{lang === 'hi' ? s.hinglishTitle : s.title}</span>
                <ArrowRight size={14} className="text-clay-600 shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* Category 3: Cold / No Heat */}
        <div className="p-4 rounded-card bg-paper border border-sand shadow-sm">
          <div className="flex items-center gap-2 mb-2 text-clay-700">
            <ThermometerSnowflake size={18} />
            <h3 className="font-display font-bold text-base text-ink">
              {lang === 'hi' ? 'ठंडा / धीमा (Cold Pile)' : 'Cold & Inactive'}
            </h3>
          </div>
          <p className="text-[11px] text-ink-muted mb-3 font-sans">
            Sitting for weeks without heating or shrinking.
          </p>
          <div className="space-y-2">
            {DOCTOR_SYMPTOMS.filter((s) => s.category === 'temp').map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => onSelectSymptom(s)}
                className="w-full text-left p-3 rounded-card bg-cream hover:bg-sand/60 border border-sand/80 text-xs font-semibold text-ink flex items-center justify-between transition-colors min-h-[48px]"
              >
                <span>{lang === 'hi' ? s.hinglishTitle : s.title}</span>
                <ArrowRight size={14} className="text-clay-600 shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* Category 4: Moisture */}
        <div className="p-4 rounded-card bg-paper border border-sand shadow-sm">
          <div className="flex items-center gap-2 mb-2 text-clay-700">
            <Droplets size={18} />
            <h3 className="font-display font-bold text-base text-ink">
              {lang === 'hi' ? 'नमी (Too Wet or Dry)' : 'Moisture Issues'}
            </h3>
          </div>
          <p className="text-[11px] text-ink-muted mb-3 font-sans">
            Sludgy dripping water or bone dry like dust.
          </p>
          <div className="space-y-2">
            {DOCTOR_SYMPTOMS.filter((s) => s.category === 'moisture').map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => onSelectSymptom(s)}
                className="w-full text-left p-3 rounded-card bg-cream hover:bg-sand/60 border border-sand/80 text-xs font-semibold text-ink flex items-center justify-between transition-colors min-h-[48px]"
              >
                <span>{lang === 'hi' ? s.hinglishTitle : s.title}</span>
                <ArrowRight size={14} className="text-clay-600 shrink-0" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
