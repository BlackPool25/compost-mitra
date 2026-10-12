import React, { useState } from 'react';
import { KitchenItem } from '../types';
import { logWasteAdd } from '../lib/storage';
import { WarliHandful, WarliSqueeze } from '../components/WarliArt';
import { Check, ArrowLeft, RotateCcw } from 'lucide-react';

interface AddResultScreenProps {
  selectedItems: { item: KitchenItem; count: number }[];
  onBack: () => void;
  onDone: () => void;
  lang: 'en' | 'hi';
}

export const AddResultScreen: React.FC<AddResultScreenProps> = ({
  selectedItems,
  onBack,
  onDone,
  lang,
}) => {
  const [logged, setLogged] = useState(false);
  const [showUndoToast, setShowUndoToast] = useState(false);

  // Compute total caddies & calculated required handfuls of browns
  // Heuristic: 1 caddy wet greens = 2 handfuls dry leaves or 1.5 handfuls coco-peat
  const totalCaddyWeight = selectedItems.reduce((acc, curr) => {
    const factor = curr.item.unit === 'caddy' ? 1.0 : curr.item.unit === 'filter' ? 0.3 : 0.4;
    return acc + curr.count * factor;
  }, 0);

  const neededHandfuls = Math.max(1, Math.round(totalCaddyWeight * 2));

  const handleLog = () => {
    const notes = selectedItems.map((s) => `${s.count} ${s.item.hinglishName}`).join(', ');
    logWasteAdd(totalCaddyWeight, neededHandfuls, notes);
    setLogged(true);
    setShowUndoToast(true);
    setTimeout(() => {
      onDone();
    }, 1800);
  };

  return (
    <div className="pb-28 max-w-lg mx-auto">
      {/* Top back navigation */}
      <button
        onClick={onBack}
        type="button"
        className="flex items-center gap-1.5 text-xs font-semibold text-clay-700 hover:text-clay-600 mb-4 min-h-[36px]"
      >
        <ArrowLeft size={16} />
        <span>{lang === 'hi' ? 'बदलाव करें' : 'Change items'}</span>
      </button>

      {/* Main Recipe Outcome Card */}
      <div className="p-6 rounded-card bg-paper border border-sand shadow-warm text-center">
        <div className="inline-block p-1 bg-cream rounded-full mb-3">
          <WarliHandful size={130} className="mx-auto" />
        </div>

        <span className="text-xs font-bold uppercase tracking-wider text-clay-700 bg-clay-200/50 px-2.5 py-1 rounded-full">
          {lang === 'hi' ? 'आज का सटीक अनुपात' : 'Today\'s Exact Recipe'}
        </span>

        <h2 className="text-2xl font-bold font-display text-ink mt-3">
          {lang === 'hi'
            ? `${neededHandfuls} मुट्ठी सूखे पत्ते डालें`
            : `Add ${neededHandfuls} handfuls of dry leaves`}
        </h2>

        <p className="text-xs text-ink-muted mt-2 font-sans max-w-sm mx-auto leading-relaxed">
          {lang === 'hi'
            ? 'आपके गीले कचरे के हिसाब से, इतनी मुट्ठी सूखे पत्ते या कोको-पीट की चादर बिछाने से C:N संतुलन 30:1 पर रहेगा और मक्खियां नहीं आएंगी।'
            : `Toss in ${neededHandfuls} handfuls of dry fallen leaves, shredded egg trays, or coco-peat right over today's scraps. Keeps carbon balanced at 30:1.`}
        </p>

        {/* What You Picked Summary */}
        <div className="my-5 p-3 rounded-card bg-cream border border-sand text-left">
          <div className="text-[11px] font-bold uppercase tracking-wider text-ink-muted mb-1.5">
            {lang === 'hi' ? 'आपका डाला गया कचरा:' : 'Items recorded:'}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {selectedItems.map((it, i) => (
              <span
                key={i}
                className="text-xs px-2.5 py-1 rounded-full bg-paper border border-sand text-ink font-medium"
              >
                {it.count}x {lang === 'hi' ? it.item.hinglishName : it.item.name}
              </span>
            ))}
          </div>
        </div>

        {/* Moisture Squeeze Reminder Card */}
        <div className="p-3.5 rounded-card bg-neem-100/60 border border-neem-700/20 text-left flex items-start gap-3">
          <WarliSqueeze size={54} className="shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-neem-700">
              {lang === 'hi' ? 'दबाने का नियम (The Squeeze Test)' : 'The Squeeze Test Check'}
            </h4>
            <p className="text-[11px] text-ink leading-relaxed mt-0.5">
              {lang === 'hi'
                ? 'खाद को मुट्ठी में दबाने पर बस 1 बूँद पानी निकलना चाहिए—जैसे निचोड़ा हुआ स्पंज।'
                : 'Pile should feel like a wrung-out damp sponge. If water drips, add 1 more handful of dry leaves.'}
            </p>
          </div>
        </div>
      </div>

      {/* Done Action Button */}
      <div className="mt-6">
        <button
          onClick={handleLog}
          disabled={logged}
          className={`w-full py-4 px-6 rounded-card font-semibold text-base flex items-center justify-center gap-2 shadow-warm transition-all duration-micro min-h-[56px] ${
            logged
              ? 'bg-neem-700 text-paper'
              : 'bg-clay-600 hover:bg-clay-700 text-paper active:scale-98'
          }`}
        >
          {logged ? (
            <>
              <Check size={20} strokeWidth={2.5} />
              <span>{lang === 'hi' ? 'पाइल में दर्ज हो गया!' : 'Logged to Pile!'}</span>
            </>
          ) : (
            <>
              <Check size={20} strokeWidth={2.5} />
              <span>{lang === 'hi' ? 'डाल दिया (Mark Added)' : 'Mark Added & Log to Pile'}</span>
            </>
          )}
        </button>
      </div>

      {/* Toast Notification with Undo */}
      {showUndoToast && (
        <div className="fixed bottom-20 left-4 right-4 z-50 max-w-sm mx-auto p-3.5 rounded-card bg-ink text-paper flex items-center justify-between shadow-elevated transition-all">
          <span className="text-xs font-medium">
            {lang === 'hi' ? 'कचरा सफलतापूर्वक लॉग हुआ' : 'Added to active pile'}
          </span>
          <button
            onClick={() => {
              setShowUndoToast(false);
              setLogged(false);
            }}
            className="flex items-center gap-1 text-xs text-haldi-500 font-bold underline ml-2"
          >
            <RotateCcw size={12} /> Undo
          </button>
        </div>
      )}
    </div>
  );
};
