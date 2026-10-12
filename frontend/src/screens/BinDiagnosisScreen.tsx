import React, { useState } from 'react';
import { DoctorSymptom } from '../types';
import { MatkaMitra } from '../components/MatkaMitra';
import { ArrowLeft, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';

interface BinDiagnosisScreenProps {
  symptom: DoctorSymptom;
  onBack: () => void;
  lang: 'en' | 'hi';
}

export const BinDiagnosisScreen: React.FC<BinDiagnosisScreenProps> = ({
  symptom,
  onBack,
  lang,
}) => {
  const [helped, setHelped] = useState(false);

  return (
    <div className="pb-28 max-w-lg mx-auto">
      {/* Top back navigation */}
      <button
        onClick={onBack}
        type="button"
        className="flex items-center gap-1.5 text-xs font-semibold text-clay-700 hover:text-clay-600 mb-4 min-h-[36px]"
      >
        <ArrowLeft size={16} />
        <span>{lang === 'hi' ? 'अन्य लक्षण देखें' : 'Pick another symptom'}</span>
      </button>

      {/* Reassurance Header */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm mb-4">
        <div className="flex items-start gap-3">
          <MatkaMitra tone="calm" size={44} className="shrink-0" />
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-neem-700 bg-neem-100 px-2 py-0.5 rounded-full">
              Mitra's Remedy
            </span>
            <h2 className="text-xl font-bold font-display text-ink mt-1">
              {lang === 'hi' ? symptom.hinglishTitle : symptom.title}
            </h2>
            <p className="text-xs text-ink-muted mt-2 font-sans italic leading-relaxed">
              "{symptom.mitraMessage}"
            </p>
          </div>
        </div>
      </div>

      {/* Root Cause Explanation */}
      <div className="p-4 rounded-card bg-cream border border-sand mb-4">
        <div className="flex items-center gap-2 text-clay-700 mb-1 text-xs font-bold uppercase tracking-wider">
          <AlertCircle size={14} />
          <span>{lang === 'hi' ? 'यह क्यों हुआ? (Root Cause)' : 'Why this happened'}</span>
        </div>
        <p className="text-xs text-ink leading-relaxed">
          {symptom.rootCause}
        </p>
      </div>

      {/* Immediate Primary Action */}
      <div className="p-5 rounded-card bg-paper border border-clay-600 shadow-warm mb-4">
        <div className="text-xs font-bold uppercase tracking-wider text-clay-700 flex items-center gap-1.5 mb-1.5">
          <Sparkles size={14} />
          {lang === 'hi' ? 'तुरंत एक काम करें:' : 'Immediate Single Action:'}
        </div>
        <h3 className="text-lg font-bold font-display text-ink leading-snug">
          {symptom.immediateAction}
        </h3>
      </div>

      {/* Step by Step Action Checklist */}
      <div className="p-5 rounded-card bg-paper border border-sand shadow-warm mb-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-ink-muted mb-3">
          {lang === 'hi' ? '3 आसान कदम (Step-by-step):' : '3 Easy Steps to Fix:'}
        </h4>
        <div className="space-y-3">
          {symptom.howToSteps.map((step, idx) => (
            <div key={idx} className="flex items-start gap-2.5">
              <span className="w-5 h-5 rounded-full bg-sand text-ink text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                {idx + 1}
              </span>
              <p className="text-xs text-ink leading-relaxed font-sans">{step}</p>
            </div>
          ))}
        </div>

        {/* Future Prevention Tip */}
        <div className="mt-4 pt-3 border-t border-sand text-[11px] text-ink-muted">
          <span className="font-semibold text-ink">
            {lang === 'hi' ? 'आगे के लिए टिप: ' : 'Future Tip: '}
          </span>
          {symptom.preventNext}
        </div>
      </div>

      {/* Did it help feedback button */}
      <div className="text-center">
        {helped ? (
          <div className="p-4 rounded-card bg-neem-100 text-neem-700 text-xs font-semibold flex items-center justify-center gap-2">
            <CheckCircle2 size={16} />
            <span>
              {lang === 'hi'
                ? 'बहुत बढ़िया! 24-48 घंटे में आपका पॉट ठीक हो जाएगा।'
                : 'Glad this helped! Your pile will re-balance within 24–48 hours.'}
            </span>
          </div>
        ) : (
          <button
            onClick={() => setHelped(true)}
            className="w-full py-4 px-6 rounded-card bg-clay-600 hover:bg-clay-700 text-paper font-semibold text-sm transition-all shadow-warm min-h-[52px]"
          >
            {lang === 'hi' ? 'मैंने यह कर दिया (Done)' : 'I have done this step'}
          </button>
        )}
      </div>
    </div>
  );
};
