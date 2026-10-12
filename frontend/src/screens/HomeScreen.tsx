import React from 'react';
import { Pile } from '../types';
import { PotMeter } from '../components/PotMeter';
import { MatkaMitra } from '../components/MatkaMitra';
import { ArrowRight, RotateCcw, Sparkles } from 'lucide-react';

interface HomeScreenProps {
  pile: Pile;
  onGoToAdd: () => void;
  onGoToDoctor: () => void;
  onGoToJourney: () => void;
  lang: 'en' | 'hi';
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  pile,
  onGoToAdd,
  onGoToDoctor,
  onGoToJourney,
  lang,
}) => {
  // Determine Mitra's expression based on pile day and state
  const getMitraState = () => {
    if (pile.state === 'act_now' || pile.state === 'too_wet') {
      return { tone: 'sniffing' as const, msg: 'Thoda dhyan chahiye: Bin mein moisture ya hawa check karein.' };
    }
    if (pile.dayCount >= 40) {
      return { tone: 'proud' as const, msg: 'Aapka compost lagbhag taiyaar hai! Khushboo mitti jaisi ho gayi.' };
    }
    if (pile.dayCount >= 4 && pile.dayCount <= 18) {
      return { tone: 'sweating' as const, msg: 'Pile garam ho gaya hai! Microbes tezi se kaam kar rahe hain. Bahut badhiya.' };
    }
    if (pile.state === 'cold_sleeping') {
      return { tone: 'sleepy' as const, msg: 'Pile aaram se so raha hai. Thoda paani ya sabzi chilke chahiye.' };
    }
    return { tone: 'calm' as const, msg: 'Sab theek chal raha hai. Roz ki tarah thoda sukha daalte rahein.' };
  };

  const mitra = getMitraState();

  return (
    <div className="space-y-5 pb-24">
      {/* Hero Card: The Matka Pot Meter & Mitra Speech */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Visual Pot Meter */}
          <div className="shrink-0">
            <PotMeter
              percent={pile.maturityPercent}
              dayCount={pile.dayCount}
              state={pile.state}
              temperatureC={pile.temperatureC}
            />
          </div>

          {/* Mitra's Calm Voice */}
          <div className="flex-1 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 mb-2">
              <MatkaMitra tone={mitra.tone} size={40} />
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-sand text-ink">
                Mitra
              </span>
            </div>
            <p className="font-display text-lg text-ink font-semibold leading-snug">
              "{mitra.msg}"
            </p>
            <p className="text-xs text-ink-muted mt-2 font-sans">
              {lang === 'hi'
                ? `कुल कचरा बचाया: ${pile.totalWasteKg} किग्रा`
                : `Diverted so far: ${pile.totalWasteKg} kg waste`}
            </p>
          </div>
        </div>
      </div>

      {/* AAJ KA KAAM (Single Primary Action Card) */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold tracking-wider uppercase text-clay-700 flex items-center gap-1.5">
            <Sparkles size={14} className="text-clay-600" />
            {lang === 'hi' ? 'आज का काम' : "Today's One Step"}
          </span>
          <span className="text-[11px] font-medium text-ink-muted bg-cream px-2 py-0.5 rounded-full border border-sand">
            30 seconds
          </span>
        </div>

        <h3 className="text-xl font-bold font-display text-ink mb-1">
          {lang === 'hi' ? '2 मुट्ठी सूखे पत्ते डालें' : 'Add 2 handfuls of dry leaves'}
        </h3>
        <p className="text-xs text-ink-muted mb-4 font-sans leading-relaxed">
          {lang === 'hi'
            ? 'ताज़ा सब्ज़ी छिलकों के ऊपर 2 मुट्ठी सूखे पत्ते या कोको-पीट की चादर बिछाएं।'
            : 'Cover today\'s fresh kitchen scraps with a brown blanket to lock in moisture and stop fruit flies.'}
        </p>

        <button
          onClick={onGoToAdd}
          className="w-full py-4 px-6 rounded-card bg-clay-600 hover:bg-clay-700 active:scale-98 text-paper font-semibold text-base flex items-center justify-center gap-2 shadow-warm transition-all duration-micro min-h-[56px]"
        >
          <span>{lang === 'hi' ? 'कचरा डालें (Add today)' : 'Log Scraps (Add Today)'}</span>
          <ArrowRight size={18} />
        </button>
      </div>

      {/* Quiet Reminder / Next Action Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Next Turn Reminder */}
        <button
          onClick={onGoToJourney}
          type="button"
          className="p-4 rounded-card bg-paper/80 border border-sand text-left hover:bg-paper transition-colors duration-micro flex items-center justify-between"
        >
          <div>
            <div className="text-xs text-ink-muted flex items-center gap-1.5">
              <RotateCcw size={13} className="text-clay-600" />
              {lang === 'hi' ? 'अगला पलटना' : 'Next Turning'}
            </div>
            <div className="text-sm font-bold text-ink mt-0.5">
              Day {pile.nextTurnDay} ({pile.nextTurnDay - pile.dayCount} days left)
            </div>
          </div>
          <span className="text-xs font-semibold text-clay-700">View timeline →</span>
        </button>

        {/* Quick Bin Doctor Check */}
        <button
          onClick={onGoToDoctor}
          type="button"
          className="p-4 rounded-card bg-paper/80 border border-sand text-left hover:bg-paper transition-colors duration-micro flex items-center justify-between"
        >
          <div>
            <div className="text-xs text-ink-muted">
              {lang === 'hi' ? 'बिन में कोई परेशानी?' : 'Bin feeling off?'}
            </div>
            <div className="text-sm font-bold text-ink mt-0.5">
              {lang === 'hi' ? 'डॉक्टर चेक (बदबू / कीड़े)' : 'Bin Doctor (Smells/Flies)'}
            </div>
          </div>
          <span className="text-xs font-semibold text-clay-700">Triage →</span>
        </button>
      </div>
    </div>
  );
};
