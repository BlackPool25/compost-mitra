import React, { useState } from 'react';
import { WarliHandful, WarliTurn, WarliSprout } from '../components/WarliArt';
import { MatkaMitra } from '../components/MatkaMitra';
import { ArrowRight } from 'lucide-react';

interface WelcomeScreenProps {
  onComplete: () => void;
  lang: 'en' | 'hi';
  onToggleLang: () => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  onComplete,
  lang,
  onToggleLang,
}) => {
  const [slide, setSlide] = useState(0);

  const cards = [
    {
      title: lang === 'hi' ? 'नमस्ते! आपका कंपोस्ट साथी' : 'Namaste! Meet CompostMitra',
      subtitle:
        lang === 'hi'
          ? 'बालकोनी में बदबू और मक्खियों के बिना खाद बनाएं — मुट्ठी के हिसाब से, ग्राम में नहीं।'
          : 'A calm, balcony-friendly guide that speaks in handfuls, not grams. No smell, no kitchen scale.',
      art: <WarliHandful size={140} className="mx-auto my-4 text-clay-600" />,
      tone: 'calm' as const,
    },
    {
      title: lang === 'hi' ? 'आज क्या डालें? बस 30 सेकंड' : 'What to add today, in 30 seconds',
      subtitle:
        lang === 'hi'
          ? '1 डब्बा सब्ज़ी छिलके? बस 2 मुट्ठी सूखे पत्ते या कोको-पीट डालें। अनुपात हमेशा संतुलित।'
          : 'Got a bowl of kitchen peels? Just toss in 2 handfuls of dry leaves or coco-peat. Perfectly balanced.',
      art: <WarliTurn size={140} className="mx-auto my-4 text-clay-600" />,
      tone: 'sweating' as const,
    },
    {
      title: lang === 'hi' ? '45 दिन में पौधों का अमृत' : 'Black gold for your pots in 45 days',
      subtitle:
        lang === 'hi'
          ? 'टमाटर, तुलसी और गुलाब के लिए सुरक्षित और परिपक्व खाद। 100% ऑफलाइन, ज़ीरो हार्डवेयर।'
          : 'Cured, living organic compost for your tomatoes, tulsi, and roses. Works 100% offline, ₹0 hardware.',
      art: <WarliSprout size={140} className="mx-auto my-4 text-neem-700" />,
      tone: 'proud' as const,
    },
  ];

  return (
    <div className="min-h-screen bg-cream flex flex-col justify-between p-6 max-w-lg mx-auto">
      {/* Top Header with Language Pill */}
      <div className="flex items-center justify-between pt-2">
        <div className="flex items-center gap-2">
          <MatkaMitra tone={cards[slide].tone} size={40} />
          <span className="font-display font-bold text-lg text-ink">CompostMitra</span>
        </div>
        <button
          onClick={onToggleLang}
          className="text-xs font-semibold px-3 py-1 rounded-full border border-sand bg-paper text-ink"
        >
          {lang === 'hi' ? 'English' : 'हिंदी'}
        </button>
      </div>

      {/* Main Card Content */}
      <div className="my-auto py-6 text-center">
        <div className="p-6 rounded-card bg-paper border border-sand shadow-warm transition-all duration-std">
          {cards[slide].art}
          <h2 className="text-2xl font-bold font-display text-ink mt-3">
            {cards[slide].title}
          </h2>
          <p className="text-sm text-ink-muted mt-3 leading-relaxed font-sans max-w-sm mx-auto">
            {cards[slide].subtitle}
          </p>
        </div>

        {/* Stepper Dots */}
        <div className="flex justify-center gap-2 mt-6">
          {cards.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setSlide(idx)}
              aria-label={`Go to slide ${idx + 1}`}
              className={`h-2 rounded-full transition-all duration-micro ${
                slide === idx ? 'w-6 bg-clay-600' : 'w-2 bg-sand'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-3 pb-6">
        {slide < cards.length - 1 ? (
          <button
            onClick={() => setSlide(slide + 1)}
            className="w-full py-4 px-6 rounded-card bg-clay-600 hover:bg-clay-700 active:scale-98 text-paper font-semibold text-base flex items-center justify-center gap-2 shadow-warm transition-all duration-micro min-h-[56px]"
          >
            <span>{lang === 'hi' ? 'आगे बढ़ें' : 'Next'}</span>
            <ArrowRight size={18} />
          </button>
        ) : (
          <button
            onClick={onComplete}
            className="w-full py-4 px-6 rounded-card bg-clay-600 hover:bg-clay-700 active:scale-98 text-paper font-semibold text-base flex items-center justify-center gap-2 shadow-elevated transition-all duration-micro min-h-[56px]"
          >
            <span>{lang === 'hi' ? 'शुरू करें (ज़ीरो साइन-अप)' : 'Start My First Pile (No Sign-up)'}</span>
            <ArrowRight size={18} />
          </button>
        )}

        {slide < cards.length - 1 && (
          <button
            onClick={onComplete}
            className="w-full py-2 text-xs font-semibold text-ink-muted hover:text-ink text-center"
          >
            {lang === 'hi' ? 'सीधे शुरू करें' : 'Skip walkthrough'}
          </button>
        )}
      </div>
    </div>
  );
};
