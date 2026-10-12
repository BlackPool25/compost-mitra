import React, { useState, useEffect } from 'react';
import { Pile, KitchenItem, DoctorSymptom } from './types';
import { getActivePile } from './lib/storage';
import { Header } from './components/Header';
import { Navbar, NavTab } from './components/Navbar';
import { WelcomeScreen } from './screens/WelcomeScreen';
import { SetupPileScreen } from './screens/SetupPileScreen';
import { HomeScreen } from './screens/HomeScreen';
import { AddTodayScreen } from './screens/AddTodayScreen';
import { AddResultScreen } from './screens/AddResultScreen';
import { BinDoctorScreen } from './screens/BinDoctorScreen';
import { BinDiagnosisScreen } from './screens/BinDiagnosisScreen';
import { PileJourneyScreen } from './screens/PileJourneyScreen';
import { HarvestScreen } from './screens/HarvestScreen';
import { PlantsDosingScreen } from './screens/PlantsDosingScreen';
import { ImpactScreen } from './screens/ImpactScreen';
import { MoreScreen } from './screens/MoreScreen';
import { BookOpen, Sparkles, Sprout, Wind, Check } from 'lucide-react';

export function App() {
  const [lang, setLang] = useState<'en' | 'hi'>('en');
  const [isOnboarding, setIsOnboarding] = useState<boolean>(() => {
    return !localStorage.getItem('compostmitra_onboarding_done');
  });
  const [isSettingUpPile, setIsSettingUpPile] = useState<boolean>(false);
  const [currentTab, setCurrentTab] = useState<NavTab>('home');

  // Sub-navigation states
  const [selectedScraps, setSelectedScraps] = useState<{ item: KitchenItem; count: number }[]>([]);
  const [selectedSymptom, setSelectedSymptom] = useState<DoctorSymptom | null>(null);
  const [moreSubView, setMoreSubView] = useState<'menu' | 'plants' | 'impact'>('menu');
  const [isHarvestView, setIsHarvestView] = useState<boolean>(false);

  // Pile State
  const [pile, setPile] = useState<Pile>(getActivePile);

  // Sync pile on storage events or updates
  const refreshPile = () => {
    setPile(getActivePile());
  };

  const toggleLang = () => {
    setLang((prev) => (prev === 'en' ? 'hi' : 'en'));
  };

  const handleFinishOnboarding = () => {
    localStorage.setItem('compostmitra_onboarding_done', 'true');
    setIsOnboarding(false);
  };

  // If user is on onboarding welcome screen
  if (isOnboarding) {
    return (
      <WelcomeScreen
        onComplete={() => {
          setIsSettingUpPile(true);
          setIsOnboarding(false);
        }}
        lang={lang}
        onToggleLang={toggleLang}
      />
    );
  }

  // If user is setting up a new pile
  if (isSettingUpPile) {
    return (
      <SetupPileScreen
        onDone={() => {
          localStorage.setItem('compostmitra_onboarding_done', 'true');
          setIsSettingUpPile(false);
          refreshPile();
          setCurrentTab('home');
        }}
        lang={lang}
      />
    );
  }

  return (
    <div className="min-h-screen bg-cream text-ink font-sans flex flex-col">
      {/* Top Application Header */}
      <Header lang={lang} onToggleLang={toggleLang} isOffline={!navigator.onLine} />

      {/* Main Responsive Grid Layout (Desktop Rail + Main Content + Side Panel) */}
      <div className="flex-1 flex max-w-7xl mx-auto w-full">
        {/* Navigation (Left Rail on lg: / Bottom Nav on mobile) */}
        <Navbar
          currentTab={currentTab}
          onSelectTab={(tab) => {
            setCurrentTab(tab);
            // Reset sub-views when clicking nav items
            if (tab === 'add') setSelectedScraps([]);
            if (tab === 'doctor') setSelectedSymptom(null);
            if (tab === 'pile') setIsHarvestView(false);
            if (tab === 'more') setMoreSubView('menu');
          }}
          lang={lang}
        />

        {/* Central Working Screen Column (Max 560px for mobile ergonomics) */}
        <main className="flex-1 lg:pl-64 px-4 pt-4 pb-12 max-w-xl mx-auto w-full">
          {/* TAB 1: HOME */}
          {currentTab === 'home' && (
            <HomeScreen
              pile={pile}
              onGoToAdd={() => setCurrentTab('add')}
              onGoToDoctor={() => setCurrentTab('doctor')}
              onGoToJourney={() => setCurrentTab('pile')}
              lang={lang}
            />
          )}

          {/* TAB 2: JOURNEY / PILE */}
          {currentTab === 'pile' && (
            <>
              {isHarvestView ? (
                <HarvestScreen
                  onBack={() => setIsHarvestView(false)}
                  onGoToDosing={() => {
                    setCurrentTab('more');
                    setMoreSubView('plants');
                  }}
                  lang={lang}
                />
              ) : (
                <PileJourneyScreen
                  pile={pile}
                  onRefresh={refreshPile}
                  onGoToHarvest={() => setIsHarvestView(true)}
                  lang={lang}
                />
              )}
            </>
          )}

          {/* TAB 3: ADD TODAY */}
          {currentTab === 'add' && (
            <>
              {selectedScraps.length > 0 ? (
                <AddResultScreen
                  selectedItems={selectedScraps}
                  onBack={() => setSelectedScraps([])}
                  onDone={() => {
                    refreshPile();
                    setSelectedScraps([]);
                    setCurrentTab('home');
                  }}
                  lang={lang}
                />
              ) : (
                <AddTodayScreen
                  onBack={() => setCurrentTab('home')}
                  onCalculate={(items) => setSelectedScraps(items)}
                  lang={lang}
                />
              )}
            </>
          )}

          {/* TAB 4: BIN DOCTOR */}
          {currentTab === 'doctor' && (
            <>
              {selectedSymptom ? (
                <BinDiagnosisScreen
                  symptom={selectedSymptom}
                  onBack={() => setSelectedSymptom(null)}
                  lang={lang}
                />
              ) : (
                <BinDoctorScreen
                  onSelectSymptom={(s) => setSelectedSymptom(s)}
                  lang={lang}
                />
              )}
            </>
          )}

          {/* TAB 5: MORE */}
          {currentTab === 'more' && (
            <>
              {moreSubView === 'plants' ? (
                <div>
                  <button
                    onClick={() => setMoreSubView('menu')}
                    className="text-xs font-semibold text-clay-700 hover:text-clay-600 mb-4 min-h-[36px]"
                  >
                    ← {lang === 'hi' ? 'वापस' : 'Back to menu'}
                  </button>
                  <PlantsDosingScreen lang={lang} />
                </div>
              ) : moreSubView === 'impact' ? (
                <div>
                  <button
                    onClick={() => setMoreSubView('menu')}
                    className="text-xs font-semibold text-clay-700 hover:text-clay-600 mb-4 min-h-[36px]"
                  >
                    ← {lang === 'hi' ? 'वापस' : 'Back to menu'}
                  </button>
                  <ImpactScreen pile={pile} lang={lang} />
                </div>
              ) : (
                <MoreScreen
                  onGoToPlants={() => setMoreSubView('plants')}
                  onGoToImpact={() => setMoreSubView('impact')}
                  onNewPile={() => setIsSettingUpPile(true)}
                  lang={lang}
                  onToggleLang={toggleLang}
                />
              )}
            </>
          )}
        </main>

        {/* Desktop Context Side Panel (Visible on large screens >= 1200px) */}
        <aside
          aria-label="Balcony Context Side Panel"
          className="hidden xl:block w-80 p-6 border-l border-sand bg-paper/60 space-y-6"
        >
          {/* Quick Active Matka Summary */}
          <div className="p-4 rounded-card bg-paper border border-sand shadow-warm">
            <span className="text-[10px] font-bold uppercase tracking-wider text-clay-700 bg-clay-200/50 px-2 py-0.5 rounded-full">
              Active Container
            </span>
            <h4 className="font-display font-bold text-base text-ink mt-2">
              {pile.name}
            </h4>
            <div className="text-xs text-ink-muted mt-1 space-y-1">
              <div>Day {pile.dayCount} · {pile.maturityPercent}% Matured</div>
              <div>Container: {pile.size.toUpperCase()}</div>
              <div>Estimated Temp: {pile.temperatureC || 52}°C (Thermophilic)</div>
            </div>
          </div>

          {/* Quick Balcony Composting Tips */}
          <div className="p-4 rounded-card bg-cream border border-sand space-y-3 text-xs">
            <div className="font-bold text-ink font-display flex items-center gap-1.5">
              <Sparkles size={14} className="text-clay-600" />
              Balcony Pro-Tip
            </div>
            <p className="text-ink-muted leading-relaxed">
              Always cover fresh green food scraps with a 1-inch "brown blanket" of crushed dry leaves, coco-peat, or cardboard. This traps moisture and eliminates fruit flies completely!
            </p>
          </div>

          {/* Science & Honesty Badge */}
          <div className="p-4 rounded-card bg-sand/30 border border-sand text-[11px] text-ink-muted space-y-2">
            <div className="font-semibold text-ink flex items-center gap-1.5">
              <BookOpen size={13} className="text-clay-700" />
              The Mitra Contract
            </div>
            <p className="leading-relaxed">
              Compost builds living soil biology and organic matter. Handfuls, not grams. No hardware sensors needed.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default App;
