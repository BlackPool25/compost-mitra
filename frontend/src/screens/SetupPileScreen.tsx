import React, { useState } from 'react';
import { PileSize } from '../types';
import { resetPile } from '../lib/storage';
import { MatkaMitra } from '../components/MatkaMitra';
import { Check } from 'lucide-react';

interface SetupPileScreenProps {
  onDone: () => void;
  lang: 'en' | 'hi';
}

export const SetupPileScreen: React.FC<SetupPileScreenProps> = ({ onDone, lang }) => {
  const [size, setSize] = useState<PileSize>('matka');
  const [name, setName] = useState('Balcony Matka #1');

  const options: { id: PileSize; label: string; desc: string; hinglishDesc: string }[] = [
    {
      id: 'matka',
      label: lang === 'hi' ? 'मिट्टी का मटका / खंभा' : 'Terracotta Matka / Kambha',
      desc: '15–20 Litres terracotta pot or stack. Breathable clay walls prevent smells naturally.',
      hinglishDesc: '15-20L mitti ka dabba ya pot. Natural aeration se badbu nahi aati.',
    },
    {
      id: 'bucket',
      label: lang === 'hi' ? 'हवादार प्लास्टिक बाल्टी' : 'Aerated Plastic Bucket',
      desc: '20L domestic bucket with drilled air holes on sides and bottom drainage.',
      hinglishDesc: '20L bucket jisme chhed kiye ho. Balcony utility ke liye badhiya.',
    },
    {
      id: 'drum',
      label: lang === 'hi' ? 'बड़ा ड्रम / कम्पोस्ट टम्बलर' : 'Terrace Drum / Tumbler',
      desc: '40–60L large container for joint families or high daily vegetable scraps.',
      hinglishDesc: '40-60L chhat ke liye. Zyada kachre ke liye best.',
    },
    {
      id: 'bed',
      label: lang === 'hi' ? 'गार्डन क्यारी / जाली' : 'Garden Bed / Wire Cage',
      desc: '100L+ ground heap or wire-mesh leaf cage for outdoor gardens.',
      hinglishDesc: '100L+ zameen par compost pile.',
    },
  ];

  const handleCreate = () => {
    resetPile(name, size);
    onDone();
  };

  return (
    <div className="min-h-screen bg-cream p-6 max-w-lg mx-auto flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-3 pt-2 mb-6">
          <MatkaMitra tone="calm" size={44} />
          <div>
            <h2 className="text-2xl font-bold font-display text-ink">
              {lang === 'hi' ? 'नया पाइल सेट करें' : 'Set up your compost pile'}
            </h2>
            <p className="text-xs text-ink-muted font-sans">
              {lang === 'hi' ? 'बस दो टैप में शुरू करें' : 'Two taps to get started'}
            </p>
          </div>
        </div>

        {/* Pile Name Input */}
        <div className="mb-6">
          <label className="block text-xs font-semibold text-ink-muted uppercase tracking-wider mb-2">
            {lang === 'hi' ? 'पाइल का नाम' : 'Pile Name'}
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-4 py-3 rounded-card bg-paper border border-sand text-ink font-semibold text-base focus:border-clay-600 focus:outline-none transition-colors"
            placeholder="e.g. Balcony Khamba"
          />
        </div>

        {/* Size Selection Cards */}
        <div>
          <label className="block text-xs font-semibold text-ink-muted uppercase tracking-wider mb-2">
            {lang === 'hi' ? 'बर्तन का प्रकार चुनें' : 'Choose Container Type'}
          </label>
          <div className="space-y-3">
            {options.map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setSize(opt.id)}
                className={`w-full p-4 rounded-card border text-left flex items-start justify-between transition-all duration-micro min-h-[56px] ${
                  size === opt.id
                    ? 'bg-paper border-clay-600 shadow-warm ring-1 ring-clay-600'
                    : 'bg-paper/70 border-sand hover:bg-paper'
                }`}
              >
                <div className="pr-3">
                  <div className="font-semibold text-base text-ink flex items-center gap-2">
                    {opt.label}
                  </div>
                  <p className="text-xs text-ink-muted mt-1 leading-relaxed">
                    {lang === 'hi' ? opt.hinglishDesc : opt.desc}
                  </p>
                </div>
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 border ${
                    size === opt.id
                      ? 'bg-clay-600 border-clay-600 text-paper'
                      : 'border-sand bg-cream'
                  }`}
                >
                  {size === opt.id && <Check size={12} strokeWidth={3} />}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="pt-8 pb-4">
        <button
          onClick={handleCreate}
          className="w-full py-4 px-6 rounded-card bg-clay-600 hover:bg-clay-700 active:scale-98 text-paper font-semibold text-base shadow-warm transition-all duration-micro min-h-[56px]"
        >
          {lang === 'hi' ? 'पाइल शुरू करें' : 'Create Pile & Start'}
        </button>
      </div>
    </div>
  );
};
