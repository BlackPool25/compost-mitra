import React, { useState } from 'react';
import { KITCHEN_ITEMS } from '../data/feedstocks';
import { KitchenItem } from '../types';
import { Camera, AlertCircle, ArrowLeft, Plus, Minus, ArrowRight } from 'lucide-react';

interface AddTodayScreenProps {
  onBack: () => void;
  onCalculate: (selectedItems: { item: KitchenItem; count: number }[]) => void;
  lang: 'en' | 'hi';
}

export const AddTodayScreen: React.FC<AddTodayScreenProps> = ({
  onBack,
  onCalculate,
  lang,
}) => {
  // Counts of selected items
  const [counts, setCounts] = useState<Record<string, number>>({
    sabzi_chilke: 1, // default 1 caddy
    chai_patti: 0,
    banana_peel: 0,
    onion_garlic: 0,
  });

  // Blocked modal alert
  const [blockedAlert, setBlockedAlert] = useState<KitchenItem | null>(null);

  const handleIncrement = (item: KitchenItem) => {
    if (item.category === 'blocked') {
      setBlockedAlert(item);
      return;
    }
    setCounts((prev) => ({
      ...prev,
      [item.id]: (prev[item.id] || 0) + 1,
    }));
  };

  const handleDecrement = (item: KitchenItem) => {
    setCounts((prev) => ({
      ...prev,
      [item.id]: Math.max(0, (prev[item.id] || 0) - 1),
    }));
  };

  const handlePhotoScan = () => {
    // Simulates quick edge camera detection
    setCounts((prev) => ({
      ...prev,
      sabzi_chilke: (prev.sabzi_chilke || 0) + 1,
      banana_peel: (prev.banana_peel || 0) + 1,
    }));
  };

  const hasAnySelected = Object.values(counts).some((c) => c > 0);

  const handleSubmit = () => {
    const list = KITCHEN_ITEMS.filter((it) => (counts[it.id] || 0) > 0).map((it) => ({
      item: it,
      count: counts[it.id],
    }));
    onCalculate(list);
  };

  return (
    <div className="pb-28">
      {/* Top Bar */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={onBack}
          type="button"
          className="flex items-center gap-1.5 text-xs font-semibold text-clay-700 hover:text-clay-600 min-h-[36px]"
        >
          <ArrowLeft size={16} />
          <span>{lang === 'hi' ? 'वापस' : 'Back'}</span>
        </button>
        <span className="text-xs font-semibold text-ink-muted">
          {lang === 'hi' ? 'कदम 1 / 2' : 'Step 1 of 2'}
        </span>
      </div>

      <div className="mb-5">
        <h2 className="text-2xl font-bold font-display text-ink">
          {lang === 'hi' ? 'आज क्या है आपके पास?' : 'What scraps do you have today?'}
        </h2>
        <p className="text-xs text-ink-muted mt-1 font-sans">
          {lang === 'hi'
            ? 'रसोई के बर्तनों के हिसाब से चुनें (कोई तोलने की ज़रूरत नहीं)'
            : 'Select kitchen volumes. No gram scale required.'}
        </p>
      </div>

      {/* Quick Camera Ingestion Option */}
      <div className="p-3.5 rounded-card bg-paper border border-sand mb-5 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full bg-sand flex items-center justify-center text-clay-700">
            <Camera size={18} />
          </div>
          <div>
            <div className="text-xs font-bold text-ink">
              {lang === 'hi' ? 'डब्बे की फोटो खींचें' : 'Snap Scrap Photo'}
            </div>
            <div className="text-[11px] text-ink-muted">
              {lang === 'hi' ? 'कैमरा से वॉल्यूम का अंदाज़ा' : 'Auto-estimates kitchen volume'}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={handlePhotoScan}
          className="px-3 py-1.5 rounded-full text-xs font-semibold bg-clay-200/60 text-clay-700 hover:bg-clay-200 transition-colors"
        >
          {lang === 'hi' ? 'स्कैन करें' : 'Scan'}
        </button>
      </div>

      {/* Kitchen Items Grid */}
      <div className="space-y-2.5">
        {KITCHEN_ITEMS.map((item) => {
          const count = counts[item.id] || 0;
          const isBlocked = item.category === 'blocked';

          return (
            <div
              key={item.id}
              className={`p-3.5 rounded-card border transition-all duration-micro flex items-center justify-between min-h-[56px] ${
                isBlocked
                  ? 'bg-paper/40 border-dashed border-sand opacity-80'
                  : count > 0
                  ? 'bg-paper border-clay-600 shadow-sm ring-1 ring-clay-600'
                  : 'bg-paper/80 border-sand hover:bg-paper'
              }`}
            >
              <div>
                <div className="font-semibold text-sm text-ink flex items-center gap-2">
                  <span>{lang === 'hi' ? item.hinglishName : item.name}</span>
                  {isBlocked && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-sand text-ink-muted font-normal">
                      Do not add
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-ink-muted mt-0.5">
                  {item.unitLabel}
                </div>
              </div>

              {/* Stepper / Action button */}
              {isBlocked ? (
                <button
                  type="button"
                  onClick={() => handleIncrement(item)}
                  className="px-2.5 py-1 text-xs text-clay-700 underline font-medium"
                >
                  Why?
                </button>
              ) : (
                <div className="flex items-center gap-2.5">
                  {count > 0 && (
                    <button
                      type="button"
                      onClick={() => handleDecrement(item)}
                      aria-label={`Decrease ${item.name}`}
                      className="w-8 h-8 rounded-full border border-sand bg-cream flex items-center justify-center text-ink active:scale-90 transition-transform"
                    >
                      <Minus size={14} />
                    </button>
                  )}
                  {count > 0 && (
                    <span className="w-5 text-center font-bold text-sm text-ink">
                      {count}
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => handleIncrement(item)}
                    aria-label={`Add ${item.name}`}
                    className={`w-8 h-8 rounded-full flex items-center justify-center active:scale-90 transition-transform ${
                      count > 0
                        ? 'bg-clay-600 text-paper'
                        : 'border border-sand bg-paper hover:bg-sand text-ink'
                    }`}
                  >
                    <Plus size={14} />
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Blocked Explanation Modal */}
      {blockedAlert && (
        <div className="fixed inset-0 z-50 bg-ink/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-paper p-5 rounded-card border border-sand max-w-sm w-full shadow-elevated">
            <div className="flex items-center gap-2 text-clay-700 mb-2">
              <AlertCircle size={20} />
              <h4 className="font-display font-bold text-base text-ink">
                {lang === 'hi' ? 'यह क्यों नहीं डालना चाहिए?' : 'Why avoid this item?'}
              </h4>
            </div>
            <p className="text-xs text-ink-muted leading-relaxed font-sans mb-4">
              {blockedAlert.explanationIfBlocked}
            </p>
            <button
              onClick={() => setBlockedAlert(null)}
              className="w-full py-2.5 rounded-card bg-clay-600 text-paper font-semibold text-xs"
            >
              Samajh gaya (Understood)
            </button>
          </div>
        </div>
      )}

      {/* Floating Continue Button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-paper/95 border-t border-sand backdrop-blur-md lg:static lg:bg-transparent lg:border-0 lg:p-0 lg:mt-6 z-30">
        <button
          onClick={handleSubmit}
          disabled={!hasAnySelected}
          className={`w-full py-4 px-6 rounded-card font-semibold text-base flex items-center justify-center gap-2 shadow-warm transition-all duration-micro min-h-[56px] ${
            hasAnySelected
              ? 'bg-clay-600 hover:bg-clay-700 text-paper active:scale-98'
              : 'bg-sand text-ink-muted cursor-not-allowed'
          }`}
        >
          <span>{lang === 'hi' ? 'खाद का संतुलन देखें' : 'Calculate Browns Balance'}</span>
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
};
