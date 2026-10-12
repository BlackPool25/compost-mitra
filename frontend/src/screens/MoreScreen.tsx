import React, { useState } from 'react';
import { Sprout, BarChart3, BookOpen, ShieldCheck, RefreshCw, ChevronRight, Check } from 'lucide-react';
import { MatkaMitra } from '../components/MatkaMitra';

interface MoreScreenProps {
  onGoToPlants: () => void;
  onGoToImpact: () => void;
  onNewPile: () => void;
  lang: 'en' | 'hi';
  onToggleLang: () => void;
}

export const MoreScreen: React.FC<MoreScreenProps> = ({
  onGoToPlants,
  onGoToImpact,
  onNewPile,
  lang,
  onToggleLang,
}) => {
  const [showScience, setShowScience] = useState(false);

  return (
    <div className="pb-28 max-w-lg mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 rounded-card bg-paper border border-sand">
        <MatkaMitra tone="calm" size={44} />
        <div>
          <h2 className="text-xl font-bold font-display text-ink">
            {lang === 'hi' ? 'अन्य विकल्प और ज्ञान' : 'More Options & Knowledge'}
          </h2>
          <p className="text-xs text-ink-muted">
            {lang === 'hi' ? 'पौधे, प्रभाव, और वैज्ञानिक प्रमाण' : 'Plant guides, impact & science'}
          </p>
        </div>
      </div>

      {/* Navigation Options List */}
      <div className="space-y-2.5">
        {/* Option 1: Plants & Dosing */}
        <button
          onClick={onGoToPlants}
          type="button"
          className="w-full p-4 rounded-card bg-paper border border-sand hover:bg-cream flex items-center justify-between text-left transition-colors min-h-[56px]"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-neem-100 text-neem-700 flex items-center justify-center">
              <Sprout size={18} />
            </div>
            <div>
              <div className="font-semibold text-sm text-ink">
                {lang === 'hi' ? 'गमलों में खाद का नियम' : 'Plant Dosing & Care'}
              </div>
              <div className="text-[11px] text-ink-muted">
                Tomato, Tulsi, Chilli, Rose handful dosages
              </div>
            </div>
          </div>
          <ChevronRight size={18} className="text-clay-600" />
        </button>

        {/* Option 2: Impact & Savings */}
        <button
          onClick={onGoToImpact}
          type="button"
          className="w-full p-4 rounded-card bg-paper border border-sand hover:bg-cream flex items-center justify-between text-left transition-colors min-h-[56px]"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-haldi-100 text-haldi-text flex items-center justify-center">
              <BarChart3 size={18} />
            </div>
            <div>
              <div className="font-semibold text-sm text-ink">
                {lang === 'hi' ? 'पर्यावरण प्रभाव और बचत' : 'Impact & Nursery Savings'}
              </div>
              <div className="text-[11px] text-ink-muted">
                kg diverted, ₹ saved, avoided methane
              </div>
            </div>
          </div>
          <ChevronRight size={18} className="text-clay-600" />
        </button>

        {/* Option 3: "How We Know" Science Modal */}
        <button
          onClick={() => setShowScience(true)}
          type="button"
          className="w-full p-4 rounded-card bg-paper border border-sand hover:bg-cream flex items-center justify-between text-left transition-colors min-h-[56px]"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-clay-200 text-clay-700 flex items-center justify-center">
              <BookOpen size={18} />
            </div>
            <div>
              <div className="font-semibold text-sm text-ink">
                {lang === 'hi' ? 'वैज्ञानिक प्रमाण (How We Know)' : 'Scientific Proof & Validation'}
              </div>
              <div className="text-[11px] text-ink-muted">
                Cornell stoichiometry & real Hafsa/Mullick datasets
              </div>
            </div>
          </div>
          <ChevronRight size={18} className="text-clay-600" />
        </button>

        {/* Option 4: Language Switcher */}
        <div className="p-4 rounded-card bg-paper border border-sand flex items-center justify-between">
          <div>
            <div className="font-semibold text-sm text-ink">
              {lang === 'hi' ? 'भाषा (Language)' : 'App Language'}
            </div>
            <div className="text-[11px] text-ink-muted">
              {lang === 'hi' ? 'वर्तमान: हिंदी / हिंग्लिश' : 'Current: English + Hinglish moments'}
            </div>
          </div>
          <button
            onClick={onToggleLang}
            className="px-3 py-1.5 rounded-full text-xs font-semibold bg-sand/60 hover:bg-sand text-ink transition-colors min-h-[36px]"
          >
            {lang === 'hi' ? 'Switch to English' : 'हिंदी में बदलें'}
          </button>
        </div>

        {/* Option 5: Reset / New Pile */}
        <button
          onClick={onNewPile}
          type="button"
          className="w-full p-4 rounded-card bg-paper border border-sand hover:bg-cream flex items-center justify-between text-left transition-colors text-clay-700 min-h-[56px]"
        >
          <div className="flex items-center gap-3">
            <RefreshCw size={18} />
            <div>
              <div className="font-semibold text-sm text-ink">
                {lang === 'hi' ? 'नया मटका शुरू करें' : 'Start a New Compost Batch'}
              </div>
              <div className="text-[11px] text-ink-muted">
                Reset or create a second container
              </div>
            </div>
          </div>
          <ChevronRight size={18} className="text-clay-600" />
        </button>
      </div>

      {/* Science & Academic Defense Modal */}
      {showScience && (
        <div className="fixed inset-0 z-50 bg-ink/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-paper p-6 rounded-card border border-sand max-w-lg w-full shadow-elevated my-8 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-sand pb-3 mb-4">
              <h3 className="font-display font-bold text-lg text-ink flex items-center gap-2">
                <ShieldCheck size={20} className="text-clay-700" />
                Scientific Grounding & Honesty
              </h3>
              <button
                onClick={() => setShowScience(false)}
                className="text-xs font-bold text-clay-700 hover:text-clay-600 px-2 py-1 rounded"
              >
                Close ✕
              </button>
            </div>

            <div className="space-y-4 text-xs text-ink-muted font-sans leading-relaxed">
              <div>
                <h4 className="font-bold text-ink text-sm">1. Zero Synthetic Training Rows</h4>
                <p>
                  All maturity predictions are grounded in real laboratory datasets: Hafsa-Kibria (452 rows), Mullick et al. (94 batches, 1,314 rows), and Zhang meta-analysis. Models are split using <code>GroupKFold</code> by experimental batch to prevent temporal data leakage.
                </p>
              </div>

              <div>
                <h4 className="font-bold text-ink text-sm">2. Deterministic Cornell Stoichiometry</h4>
                <p>
                  The Handful Balancer does not use black-box machine learning for basic arithmetic. It calculates dry-matter conservation-of-mass (Cornell 30:1 $\pm 2$ range) and bulk density tables (ASABE S269.5 & WRAP UK).
                </p>
              </div>

              <div>
                <h4 className="font-bold text-ink text-sm">3. Pathogen Safety & Curing Bioassay</h4>
                <p>
                  Thermophilic milestones are calibrated to US EPA Part 503 regulations (55°C or higher for 3 or more consecutive days). The 48-hour seed germination bioassay enforces the Zucconi Index (GI &gt;= 80%) before plant application.
                </p>
              </div>

              <div className="p-3 rounded-card bg-cream border border-sand text-ink text-[11px]">
                <strong>Canonical Agronomic Guardrail:</strong> Compost is a soil builder and organic conditioner, not a standardized chemical fertilizer replacement.
              </div>
            </div>

            <button
              onClick={() => setShowScience(false)}
              className="mt-6 w-full py-3 rounded-card bg-clay-600 text-paper font-semibold text-xs"
            >
              Close & Return
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
