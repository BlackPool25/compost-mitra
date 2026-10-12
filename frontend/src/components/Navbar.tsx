import React from 'react';
import { Home, Layers, Plus, Stethoscope, MoreHorizontal } from 'lucide-react';

export type NavTab = 'home' | 'pile' | 'add' | 'doctor' | 'more';

interface NavbarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  lang: 'en' | 'hi';
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab, lang }) => {
  const tabs = [
    {
      id: 'home' as NavTab,
      label: lang === 'hi' ? 'होम' : 'Home',
      icon: Home,
    },
    {
      id: 'pile' as NavTab,
      label: lang === 'hi' ? 'सफ़र (45d)' : 'Journey',
      icon: Layers,
    },
    // Centre Add Action is rendered separately
    {
      id: 'doctor' as NavTab,
      label: lang === 'hi' ? 'डॉक्टर' : 'Doctor',
      icon: Stethoscope,
    },
    {
      id: 'more' as NavTab,
      label: lang === 'hi' ? 'और भी' : 'More',
      icon: MoreHorizontal,
    },
  ];

  return (
    <>
      {/* Mobile Bottom Navigation Bar (hidden on lg: screens) */}
      <nav
        aria-label="Bottom Navigation"
        className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-paper/95 backdrop-blur-md border-t border-sand pb-[env(safe-area-inset-bottom)] px-3 py-2 flex items-center justify-around shadow-warm"
      >
        {/* Tab 1: Home */}
        <button
          onClick={() => onSelectTab('home')}
          className={`flex flex-col items-center justify-center min-w-[56px] min-h-[48px] py-1 transition-colors duration-micro ${
            currentTab === 'home' ? 'text-clay-600 font-semibold' : 'text-ink-muted hover:text-ink'
          }`}
        >
          <Home size={22} strokeWidth={currentTab === 'home' ? 2.5 : 1.75} />
          <span className="text-[11px] mt-0.5 leading-tight">{tabs[0].label}</span>
        </button>

        {/* Tab 2: Journey */}
        <button
          onClick={() => onSelectTab('pile')}
          className={`flex flex-col items-center justify-center min-w-[56px] min-h-[48px] py-1 transition-colors duration-micro ${
            currentTab === 'pile' ? 'text-clay-600 font-semibold' : 'text-ink-muted hover:text-ink'
          }`}
        >
          <Layers size={22} strokeWidth={currentTab === 'pile' ? 2.5 : 1.75} />
          <span className="text-[11px] mt-0.5 leading-tight">{tabs[1].label}</span>
        </button>

        {/* Centre Action Button: Raised Clay Circle */}
        <div className="relative -top-3">
          <button
            onClick={() => onSelectTab('add')}
            aria-label="Add today's waste"
            className="w-14 h-14 rounded-full bg-clay-600 text-paper flex flex-col items-center justify-center shadow-elevated border-2 border-cream active:scale-95 transition-transform duration-micro hover:bg-clay-700 focus-visible:ring-2 focus-visible:ring-clay-700"
          >
            <Plus size={26} strokeWidth={2.75} />
            <span className="text-[9px] font-bold uppercase tracking-wider -mt-0.5">
              {lang === 'hi' ? 'डालें' : 'Add'}
            </span>
          </button>
        </div>

        {/* Tab 3: Doctor */}
        <button
          onClick={() => onSelectTab('doctor')}
          className={`flex flex-col items-center justify-center min-w-[56px] min-h-[48px] py-1 transition-colors duration-micro ${
            currentTab === 'doctor' ? 'text-clay-600 font-semibold' : 'text-ink-muted hover:text-ink'
          }`}
        >
          <Stethoscope size={22} strokeWidth={currentTab === 'doctor' ? 2.5 : 1.75} />
          <span className="text-[11px] mt-0.5 leading-tight">{tabs[2].label}</span>
        </button>

        {/* Tab 4: More */}
        <button
          onClick={() => onSelectTab('more')}
          className={`flex flex-col items-center justify-center min-w-[56px] min-h-[48px] py-1 transition-colors duration-micro ${
            currentTab === 'more' ? 'text-clay-600 font-semibold' : 'text-ink-muted hover:text-ink'
          }`}
        >
          <MoreHorizontal size={22} strokeWidth={currentTab === 'more' ? 2.5 : 1.75} />
          <span className="text-[11px] mt-0.5 leading-tight">{tabs[3].label}</span>
        </button>
      </nav>

      {/* Desktop Navigation Left Rail (Visible on >= 1024px) */}
      <aside
        aria-label="Desktop Side Rail"
        className="hidden lg:flex flex-col fixed left-0 top-0 bottom-0 w-64 bg-paper border-r border-sand p-6 z-30"
      >
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl font-bold font-display text-clay-700">CompostMitra</span>
          </div>
          <p className="text-xs text-ink-muted font-sans">Terracotta Balcony Companion</p>
        </div>

        <nav className="flex flex-col gap-2 flex-1">
          <button
            onClick={() => onSelectTab('home')}
            className={`flex items-center gap-3 px-4 py-3 rounded-card text-sm font-semibold transition-colors duration-micro ${
              currentTab === 'home' ? 'bg-clay-200/50 text-clay-700' : 'text-ink hover:bg-sand/40'
            }`}
          >
            <Home size={20} /> {tabs[0].label}
          </button>

          <button
            onClick={() => onSelectTab('pile')}
            className={`flex items-center gap-3 px-4 py-3 rounded-card text-sm font-semibold transition-colors duration-micro ${
              currentTab === 'pile' ? 'bg-clay-200/50 text-clay-700' : 'text-ink hover:bg-sand/40'
            }`}
          >
            <Layers size={20} /> {tabs[1].label}
          </button>

          <button
            onClick={() => onSelectTab('doctor')}
            className={`flex items-center gap-3 px-4 py-3 rounded-card text-sm font-semibold transition-colors duration-micro ${
              currentTab === 'doctor' ? 'bg-clay-200/50 text-clay-700' : 'text-ink hover:bg-sand/40'
            }`}
          >
            <Stethoscope size={20} /> {tabs[2].label}
          </button>

          <button
            onClick={() => onSelectTab('more')}
            className={`flex items-center gap-3 px-4 py-3 rounded-card text-sm font-semibold transition-colors duration-micro ${
              currentTab === 'more' ? 'bg-clay-200/50 text-clay-700' : 'text-ink hover:bg-sand/40'
            }`}
          >
            <MoreHorizontal size={20} /> {tabs[3].label}
          </button>

          <div className="my-4 border-t border-sand" />

          {/* Dedicated Primary Action on Desktop */}
          <button
            onClick={() => onSelectTab('add')}
            className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-card bg-clay-600 text-paper font-semibold text-sm shadow-warm hover:bg-clay-700 active:scale-98 transition-all duration-micro"
          >
            <Plus size={20} strokeWidth={2.5} />
            <span>{lang === 'hi' ? 'आज का कचरा डालें' : 'Add Today\'s Waste'}</span>
          </button>
        </nav>

        {/* Footer info in rail */}
        <div className="pt-4 border-t border-sand text-xs text-ink-muted">
          <p>Terracotta & Khamba craft.</p>
          <p className="mt-1 font-mono text-[10px] text-ink-muted/80">Handfuls, not grams.</p>
        </div>
      </aside>
    </>
  );
};
