import React from 'react';
import { Pile } from '../types';
import { turnPileAction } from '../lib/storage';
import { WarliSprout } from '../components/WarliArt';
import { RotateCcw, Check, Sparkles, Sprout } from 'lucide-react';

interface PileJourneyScreenProps {
  pile: Pile;
  onRefresh: () => void;
  onGoToHarvest: () => void;
  lang: 'en' | 'hi';
}

export const PileJourneyScreen: React.FC<PileJourneyScreenProps> = ({
  pile,
  onRefresh,
  onGoToHarvest,
  lang,
}) => {
  const handleTurnPile = () => {
    turnPileAction();
    onRefresh();
  };

  const stages = [
    {
      range: 'Days 1–3',
      name: 'Mesophilic Warm-up',
      hinglishName: 'गरम शुरुआत (Mesophilic)',
      desc: 'Microbes multiply rapidly on kitchen sugars, raising initial pile temperature.',
      current: pile.dayCount <= 3,
      passed: pile.dayCount > 3,
    },
    {
      range: 'Days 4–18',
      name: 'Thermophilic Peak (50–60°C)',
      hinglishName: 'तेज़ गर्मी (Thermophilic Peak)',
      desc: 'Intense biological heat kills weed seeds, fruit fly eggs, and pathogens (EPA 503 compliant).',
      current: pile.dayCount >= 4 && pile.dayCount <= 18,
      passed: pile.dayCount > 18,
    },
    {
      range: 'Days 19–32',
      name: 'Cooling & Fungi Action',
      hinglishName: 'ठंडा होना और फफूंद (Fungi Breakdown)',
      desc: 'White fungal threads (actinomycetes) break down fibrous cardboard and tough peels.',
      current: pile.dayCount >= 19 && pile.dayCount <= 32,
      passed: pile.dayCount > 32,
    },
    {
      range: 'Days 33–45',
      name: 'Curing & Humification',
      hinglishName: 'पकना और स्थिरता (Curing & Ready)',
      desc: 'Compost stabilizes into sweet, forest-scented dark black humus. Safe for roots.',
      current: pile.dayCount >= 33,
      passed: pile.maturityPercent >= 95,
    },
  ];

  return (
    <div className="pb-28 max-w-lg mx-auto space-y-5">
      {/* Journey Banner */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm text-center">
        <WarliSprout size={90} className="mx-auto" />
        <span className="text-[11px] font-bold uppercase tracking-wider text-clay-700 bg-clay-200/50 px-2 py-0.5 rounded-full">
          Day {pile.dayCount} of 45 Days
        </span>
        <h2 className="text-2xl font-bold font-display text-ink mt-2">
          {lang === 'hi' ? '45 दिन का सफ़र' : 'The 45-Day Pile Journey'}
        </h2>
        <p className="text-xs text-ink-muted mt-1 max-w-sm mx-auto font-sans leading-relaxed">
          {lang === 'hi'
            ? 'कचरे से मिट्टी तक: आपका कम्पोस्ट किस अवस्था में है और कब क्या करना है।'
            : 'Track the living biology of your pile. From kitchen waste to balanced soil humus.'}
        </p>

        {/* Action: Turn Pile Button */}
        <div className="mt-4 pt-4 border-t border-sand flex items-center justify-between">
          <div className="text-left">
            <div className="text-xs font-bold text-ink flex items-center gap-1.5">
              <RotateCcw size={14} className="text-clay-600" />
              {lang === 'hi' ? 'पलटने का दिन' : 'Next Turning'}
            </div>
            <div className="text-[11px] text-ink-muted">
              Day {pile.nextTurnDay} ({Math.max(0, pile.nextTurnDay - pile.dayCount)} days left)
            </div>
          </div>
          <button
            onClick={handleTurnPile}
            className="px-3.5 py-2 rounded-card bg-sand/70 hover:bg-sand text-ink text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <RotateCcw size={13} />
            <span>{lang === 'hi' ? 'आज पलट दिया' : 'Mark Turned Today'}</span>
          </button>
        </div>
      </div>

      {/* 4 Stage Timeline Cards */}
      <div className="space-y-3">
        {stages.map((stage, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-card border transition-all ${
              stage.current
                ? 'bg-paper border-clay-600 shadow-warm ring-1 ring-clay-600'
                : stage.passed
                ? 'bg-paper/60 border-sand opacity-90'
                : 'bg-paper/40 border-sand opacity-70'
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold text-clay-700 font-mono">
                {stage.range}
              </span>
              {stage.current && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-clay-200 text-clay-700 flex items-center gap-1">
                  <Sparkles size={10} /> Active Now
                </span>
              )}
              {stage.passed && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-neem-100 text-neem-700 flex items-center gap-1">
                  <Check size={10} strokeWidth={3} /> Completed
                </span>
              )}
            </div>

            <h3 className="text-base font-bold font-display text-ink">
              {lang === 'hi' ? stage.hinglishName : stage.name}
            </h3>
            <p className="text-xs text-ink-muted mt-1 leading-relaxed font-sans">
              {stage.desc}
            </p>
          </div>
        ))}
      </div>

      {/* Seedling Germination Test Button (Harvest) */}
      <div className="p-4 rounded-card bg-neem-100/60 border border-neem-700/30 text-center">
        <h4 className="text-sm font-bold text-neem-700 mb-1 flex items-center justify-center gap-1.5">
          <Sprout size={16} />
          {lang === 'hi' ? 'क्या खाद तैयार है? (Curing Test)' : 'Ready for your plants?'}
        </h4>
        <p className="text-xs text-ink-muted mb-3 font-sans">
          {lang === 'hi'
            ? 'पौधों को नुकसान से बचाने के लिए 48 घंटे का सरसों/मेथी बीज टेस्ट करें।'
            : 'Run a simple 48-hour mustard/fenugreek seed check to prove your compost won\'t burn roots.'}
        </p>
        <button
          onClick={onGoToHarvest}
          className="w-full py-3 px-4 rounded-card bg-neem-700 hover:bg-neem-700/90 text-paper font-semibold text-xs transition-colors min-h-[44px]"
        >
          {lang === 'hi' ? '48-घंटे का अंकुरण टेस्ट देखें →' : 'View 48-Hour Germination Test →'}
        </button>
      </div>
    </div>
  );
};
