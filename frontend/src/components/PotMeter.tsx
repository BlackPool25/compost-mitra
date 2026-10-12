import React from 'react';
import { PileState } from '../types';

interface PotMeterProps {
  percent: number; // 0 - 100
  dayCount: number;
  state: PileState;
  temperatureC?: number;
}

export const PotMeter: React.FC<PotMeterProps> = ({
  percent,
  dayCount,
  state,
  temperatureC = 52,
}) => {
  // Clamped fill height between 5 and 90
  const fillY = Math.max(10, Math.min(88, 90 - (percent * 0.75)));

  const getStatusText = () => {
    if (dayCount <= 3) return { label: 'Warm-up', hinglish: 'Garam ho raha hai', badge: 'bg-haldi-100 text-haldi-text' };
    if (dayCount <= 18) return { label: 'Thermophilic', hinglish: `Garam hai (${temperatureC}°C)`, badge: 'bg-neem-100 text-neem-700' };
    if (dayCount <= 32) return { label: 'Cooling / Fungi', hinglish: 'Thanda ho raha hai', badge: 'bg-sand text-ink' };
    return { label: 'Curing', hinglish: 'Pak raha hai (Ready soon)', badge: 'bg-neem-100 text-neem-700' };
  };

  const status = getStatusText();

  return (
    <div
      className="relative flex flex-col items-center justify-center p-3"
      role="meter"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Pile is ${percent}% matured, currently ${status.label} on Day ${dayCount}`}
    >
      <div className="relative w-36 h-44 drop-shadow-sm">
        <svg
          viewBox="0 0 100 120"
          className="w-full h-full overflow-hidden"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Mask cutting out the exact Matka silhouette */}
            <clipPath id="matkaClip">
              <path d="M30 18 C30 26, 18 42, 14 68 C10 95, 26 112, 50 112 C74 112, 90 95, 86 68 C82 42, 70 26, 70 18 Z" />
            </clipPath>
          </defs>

          {/* Background Empty Clay Shell */}
          <path
            d="M30 18 C30 26, 18 42, 14 68 C10 95, 26 112, 50 112 C74 112, 90 95, 86 68 C82 42, 70 26, 70 18 Z"
            fill="#EADFCB"
            stroke="#9A4A32"
            strokeWidth="3"
          />

          {/* Rim of Matka */}
          <ellipse cx="50" cy="18" rx="22" ry="6" fill="#9A4A32" stroke="#6B5448" strokeWidth="1.5" />
          <ellipse cx="50" cy="16" rx="18" ry="4.5" fill="#B5523B" />

          {/* Dynamic Fill Layer clipped inside the Matka */}
          <g clipPath="url(#matkaClip)">
            {/* Dark rich compost layer */}
            <rect
              x="0"
              y={fillY}
              width="100"
              height="120"
              fill={state === 'too_wet' ? '#7A5236' : state === 'needs_browns' ? '#E0A92E' : '#B5523B'}
              className="transition-all duration-emph ease-out"
            />
            {/* Wave crest */}
            <path
              d={`M0 ${fillY} Q25 ${fillY - 3} 50 ${fillY} T100 ${fillY} L100 120 L0 120 Z`}
              fill="#9A4A32"
              opacity="0.4"
            />
          </g>

          {/* White Folk-art Ring Band on the Outside */}
          <path
            d="M26 62 Q50 68 74 62"
            stroke="#FFFDF8"
            strokeWidth="2"
            strokeDasharray="3 3"
            fill="none"
          />
        </svg>

        {/* Centered Percentage Tag on the Matka */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none pt-4">
          <span className="text-2xl font-bold font-display text-paper drop-shadow-[0_1px_2px_rgba(0,0,0,0.6)]">
            {percent}%
          </span>
          <span className="text-xs uppercase tracking-wider text-paper/90 drop-shadow-[0_1px_2px_rgba(0,0,0,0.6)] font-medium">
            Matured
          </span>
        </div>
      </div>

      {/* Pill Below Pot */}
      <div className="mt-2 flex items-center gap-1.5">
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-sand text-ink">
          Day {dayCount}
        </span>
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${status.badge}`}>
          {status.hinglish}
        </span>
      </div>
    </div>
  );
};
