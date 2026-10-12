import React from 'react';
import { Mitratone } from '../types';

interface MatkaMitraProps {
  tone?: Mitratone;
  className?: string;
  size?: number;
}

export const MatkaMitra: React.FC<MatkaMitraProps> = ({
  tone = 'calm',
  className = '',
  size = 64,
}) => {
  return (
    <div
      className={`relative inline-flex items-center justify-center transition-transform duration-micro active:scale-95 ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full drop-shadow-sm"
      >
        {/* Pot Body - Warm Terracotta Clay #B5523B with inner shading */}
        {/* Rim / Neck */}
        <ellipse cx="50" cy="24" rx="20" ry="6" fill="#9A4A32" />
        <ellipse cx="50" cy="22" rx="18" ry="5" fill="#E2725B" />
        <path
          d="M32 24 C32 30, 22 45, 20 62 C18 80, 32 90, 50 90 C68 90, 82 80, 80 62 C78 45, 68 30, 68 24 Z"
          fill="#B5523B"
        />
        {/* Clay belly highlight */}
        <path
          d="M30 62 C30 76, 40 84, 50 84 C60 84, 70 76, 70 62 C65 66, 35 66, 30 62 Z"
          fill="#9A4A32"
          opacity="0.35"
        />

        {/* Hand-painted white folk-art band (Warli motif dots) */}
        <circle cx="34" cy="48" r="1.5" fill="#FFFDF8" opacity="0.8" />
        <circle cx="42" cy="46" r="1.5" fill="#FFFDF8" opacity="0.8" />
        <circle cx="50" cy="45" r="1.5" fill="#FFFDF8" opacity="0.8" />
        <circle cx="58" cy="46" r="1.5" fill="#FFFDF8" opacity="0.8" />
        <circle cx="66" cy="48" r="1.5" fill="#FFFDF8" opacity="0.8" />

        {/* Leaf Sprout at Neck */}
        <path
          d="M50 20 C48 10, 38 8, 36 12 C34 16, 44 18, 50 20 Z"
          fill="#3F6B3A"
        />
        <path
          d="M50 20 C52 10, 62 8, 64 12 C66 16, 56 18, 50 20 Z"
          fill="#52834C"
        />

        {/* Dynamic Facial Expressions */}
        {tone === 'calm' && (
          <g stroke="#3A2218" strokeWidth="2.5" strokeLinecap="round">
            {/* Happy arched eyes */}
            <path d="M38 58 Q43 53 48 58" fill="none" />
            <path d="M52 58 Q57 53 62 58" fill="none" />
            {/* Gentle smile */}
            <path d="M44 68 Q50 74 56 68" fill="none" />
            {/* Rosy clay cheeks */}
            <circle cx="35" cy="65" r="3" fill="#F2C4B4" opacity="0.6" stroke="none" />
            <circle cx="65" cy="65" r="3" fill="#F2C4B4" opacity="0.6" stroke="none" />
          </g>
        )}

        {tone === 'sweating' && (
          <g stroke="#3A2218" strokeWidth="2.5" strokeLinecap="round">
            {/* Wide active eyes */}
            <circle cx="42" cy="57" r="2.5" fill="#3A2218" />
            <circle cx="58" cy="57" r="2.5" fill="#3A2218" />
            {/* Happy open grin */}
            <path d="M43 67 Q50 74 57 67 Z" fill="#9A4A32" />
            {/* Steam droplets */}
            <path d="M72 44 Q76 40 73 36 Q70 40 72 44 Z" fill="#E3EFD8" stroke="#3F6B3A" strokeWidth="1" />
            <path d="M78 52 Q82 48 79 44 Q76 48 78 52 Z" fill="#E3EFD8" stroke="#3F6B3A" strokeWidth="1" />
          </g>
        )}

        {tone === 'sleepy' && (
          <g stroke="#3A2218" strokeWidth="2" strokeLinecap="round">
            {/* Slanted sleepy eyes */}
            <path d="M38 58 L46 60" />
            <path d="M54 60 L62 58" />
            {/* Quiet little mouth */}
            <ellipse cx="50" cy="68" rx="2.5" ry="1.5" fill="#3A2218" />
            {/* Tiny zzz */}
            <text x="68" y="38" fill="#6B5448" fontSize="10" fontFamily="sans-serif" fontWeight="bold">z</text>
          </g>
        )}

        {tone === 'sniffing' && (
          <g stroke="#3A2218" strokeWidth="2.5" strokeLinecap="round">
            {/* Inquiring eyes */}
            <circle cx="42" cy="56" r="3" fill="#3A2218" />
            <circle cx="58" cy="56" r="3" fill="#3A2218" />
            {/* Inquisitive nose / sniff mouth */}
            <circle cx="50" cy="64" r="2" fill="#E2725B" />
            <path d="M46 70 Q50 67 54 70" fill="none" />
          </g>
        )}

        {tone === 'proud' && (
          <g stroke="#3A2218" strokeWidth="2.5" strokeLinecap="round">
            {/* Proud twinkling eyes */}
            <path d="M38 56 Q43 51 48 56" fill="none" />
            <path d="M52 56 Q57 51 62 56" fill="none" />
            <polygon points="50,48 52,52 56,53 52,56 50,60 48,56 44,53 48,52" fill="#F8E7B8" stroke="none" />
            {/* Broad happy smile */}
            <path d="M42 66 Q50 76 58 66 Z" fill="#9A4A32" />
          </g>
        )}

        {tone === 'resting' && (
          <g stroke="#3A2218" strokeWidth="2.5" strokeLinecap="round">
            {/* Peaceful straight eyes */}
            <line x1="39" y1="58" x2="47" y2="58" />
            <line x1="53" y1="58" x2="61" y2="58" />
            {/* Small calm curve */}
            <path d="M46 67 Q50 70 54 67" fill="none" />
          </g>
        )}
      </svg>
    </div>
  );
};
