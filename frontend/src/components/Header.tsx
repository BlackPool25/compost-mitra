import React from 'react';
import { Wifi, WifiOff } from 'lucide-react';
import { MatkaMitra } from './MatkaMitra';

interface HeaderProps {
  lang: 'en' | 'hi';
  onToggleLang: () => void;
  isOffline?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  lang,
  onToggleLang,
  isOffline = false,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full bg-paper/95 backdrop-blur-sm border-b border-sand px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2.5">
        <MatkaMitra tone="calm" size={36} />
        <div>
          <h1 className="text-xl font-bold font-display tracking-tight text-ink flex items-center gap-1.5 leading-none">
            CompostMitra
          </h1>
          <p className="text-[11px] text-ink-muted leading-tight font-sans">
            {lang === 'hi' ? 'आपका बालकोनी खाद साथी' : 'Balcony Composting Companion'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Offline Pill */}
        {isOffline ? (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-sand text-ink-muted">
            <WifiOff size={12} /> Offline (Local)
          </span>
        ) : (
          <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-neem-100 text-neem-700">
            <Wifi size={12} /> Ready
          </span>
        )}

        {/* Language Switcher */}
        <button
          onClick={onToggleLang}
          type="button"
          aria-label="Toggle language between English and Hindi"
          className="px-2.5 py-1 text-xs font-semibold rounded-full border border-sand bg-cream hover:bg-sand/60 text-ink transition-colors duration-micro min-h-[32px] min-w-[44px]"
        >
          {lang === 'hi' ? 'English' : 'हिंदी'}
        </button>
      </div>
    </header>
  );
};
