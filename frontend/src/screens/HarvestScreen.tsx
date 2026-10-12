import React, { useState } from 'react';
import { ArrowLeft, CheckCircle2, AlertTriangle, ArrowRight, Sprout } from 'lucide-react';

interface HarvestScreenProps {
  onBack: () => void;
  onGoToDosing: () => void;
  lang: 'en' | 'hi';
}

export const HarvestScreen: React.FC<HarvestScreenProps> = ({
  onBack,
  onGoToDosing,
  lang,
}) => {
  const [sproutedCount, setSproutedCount] = useState<number>(9);

  const isReady = sproutedCount >= 8;

  return (
    <div className="pb-28 max-w-lg mx-auto">
      {/* Top back navigation */}
      <button
        onClick={onBack}
        type="button"
        className="flex items-center gap-1.5 text-xs font-semibold text-clay-700 hover:text-clay-600 mb-4 min-h-[36px]"
      >
        <ArrowLeft size={16} />
        <span>{lang === 'hi' ? 'टाइमलाइन पर वापस' : 'Back to timeline'}</span>
      </button>

      {/* Header Card */}
      <div className="p-6 rounded-card bg-paper border border-sand shadow-warm mb-5 text-center">
        <div className="w-12 h-12 rounded-full bg-neem-100 text-neem-700 flex items-center justify-center mx-auto mb-3">
          <Sprout size={24} />
        </div>
        <span className="text-[11px] font-bold uppercase tracking-wider text-neem-700 bg-neem-100 px-2 py-0.5 rounded-full">
          Phytotoxicity Bioassay (GI ≥ 80%)
        </span>
        <h2 className="text-2xl font-bold font-display text-ink mt-2">
          {lang === 'hi' ? '48-घंटे का बीज टेस्ट' : '48-Hour Seedling Safety Test'}
        </h2>
        <p className="text-xs text-ink-muted mt-2 font-sans leading-relaxed max-w-sm mx-auto">
          {lang === 'hi'
            ? 'कच्ची खाद पौधों की जड़ों को जला सकती है। यह सरल घरेलू टेस्ट सुनिश्चित करता है कि खाद पूरी तरह परिपक्व (cured) है।'
            : 'Uncured compost contains volatile organic acids that scorch plant roots. This simple test proves your compost is sweet and cured.'}
        </p>
      </div>

      {/* How to run the test card */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm mb-5">
        <h3 className="text-sm font-bold text-ink mb-3 font-display">
          {lang === 'hi' ? 'टेस्ट कैसे करें (How to test):' : 'How to Run the 48-Hour Test:'}
        </h3>
        <ol className="space-y-3 text-xs text-ink-muted list-decimal list-inside font-sans">
          <li>
            <strong className="text-ink">Extract: </strong>
            1 चम्मच तैयार कम्पोस्ट को 1 कप पानी में घोलें और छान लें।
          </li>
          <li>
            <strong className="text-ink">Seeds: </strong>
            10 दाने सरसों (Mustard) या मेथी (Fenugreek) के बीज एक गीले टिशू पेपर पर रखें।
          </li>
          <li>
            <strong className="text-ink">Moisten: </strong>
            उस पर कम्पोस्ट के पानी की कुछ बूंदें डालें और प्लेट से ढक दें।
          </li>
          <li>
            <strong className="text-ink">Result: </strong>
            48 घंटे बाद देखें कितने बीज अंकुरित हुए।
          </li>
        </ol>
      </div>

      {/* Seed Counter Stepper */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm mb-5 text-center">
        <span className="text-xs font-semibold text-ink-muted uppercase tracking-wider">
          {lang === 'hi' ? 'कितने बीज अंकुरित हुए? (10 में से)' : 'How many seeds sprouted? (out of 10)'}
        </span>
        <div className="flex items-center justify-center gap-4 my-4">
          <button
            onClick={() => setSproutedCount((c) => Math.max(0, c - 1))}
            className="w-10 h-10 rounded-full border border-sand bg-cream text-lg font-bold text-ink active:scale-95"
          >
            -
          </button>
          <span className="text-3xl font-display font-bold text-ink w-12">
            {sproutedCount}
          </span>
          <button
            onClick={() => setSproutedCount((c) => Math.min(10, c + 1))}
            className="w-10 h-10 rounded-full border border-sand bg-cream text-lg font-bold text-ink active:scale-95"
          >
            +
          </button>
        </div>

        {/* Evaluation Verdict */}
        {isReady ? (
          <div className="p-3.5 rounded-card bg-neem-100 text-neem-700 text-xs font-semibold flex items-center justify-center gap-2">
            <CheckCircle2 size={16} />
            <span>
              {lang === 'hi'
                ? 'प्रमाणित: 80%+ अंकुरण! खाद पूरी तरह सुरक्षित और परिपक्व है।'
                : 'Certified: 80%+ Germination Index. Cured and 100% root-safe!'}
            </span>
          </div>
        ) : (
          <div className="p-3.5 rounded-card bg-haldi-100 text-haldi-text text-xs font-semibold flex items-center justify-center gap-2">
            <AlertTriangle size={16} />
            <span>
              {lang === 'hi'
                ? 'अभी थोड़ा और पकना बाकी है। 7 दिन और हवादार रखें।'
                : 'Compost is still curing. Give it 7 more days of resting.'}
            </span>
          </div>
        )}
      </div>

      {/* Next: Go to Crop Dosing */}
      <button
        onClick={onGoToDosing}
        className="w-full py-4 px-6 rounded-card bg-clay-600 hover:bg-clay-700 active:scale-98 text-paper font-semibold text-sm flex items-center justify-center gap-2 shadow-warm min-h-[56px] transition-all"
      >
        <span>{lang === 'hi' ? 'गमलों में खाद डालने का नियम देखें' : 'View Plant Dosing Guide'}</span>
        <ArrowRight size={18} />
      </button>
    </div>
  );
};
