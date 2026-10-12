import React from 'react';

interface WarliProps {
  className?: string;
  size?: number;
}

/** Warli figure holding out a handful of dry leaves */
export const WarliHandful: React.FC<WarliProps> = ({ className = '', size = 120 }) => (
  <svg
    viewBox="0 0 140 120"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{ width: size, height: (size * 120) / 140 }}
    className={className}
  >
    {/* Head */}
    <circle cx="45" cy="30" r="10" stroke="#FFFDF8" strokeWidth="2.5" fill="#3A2218" />
    <path d="M43 24 Q48 18 53 24" stroke="#FFFDF8" strokeWidth="2" fill="none" />

    {/* Upper & Lower Body Triangles */}
    <polygon points="45,40 30,62 60,62" stroke="#FFFDF8" strokeWidth="2.5" fill="#3A2218" />
    <polygon points="45,84 30,62 60,62" stroke="#FFFDF8" strokeWidth="2.5" fill="#3A2218" />

    {/* Legs */}
    <path d="M36 84 L30 108" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" />
    <path d="M54 84 L60 108" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" />

    {/* Left Arm resting on hip */}
    <path d="M30 45 L18 55 L26 68" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

    {/* Right Arm extended holding handful of leaves */}
    <path d="M60 45 L85 40 L105 48" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

    {/* Handful of Leaves (mutthi) */}
    <ellipse cx="108" cy="48" rx="6" ry="4" fill="#E2725B" stroke="#FFFDF8" strokeWidth="1.5" />
    <path d="M104 44 Q112 36 118 42" stroke="#3F6B3A" strokeWidth="2.5" fill="none" />
    <path d="M110 48 Q120 45 122 52" stroke="#3F6B3A" strokeWidth="2.5" fill="none" />
    <path d="M106 52 Q114 58 120 54" stroke="#3F6B3A" strokeWidth="2.5" fill="none" />

    {/* Target Pot on Ground */}
    <path d="M100 80 Q100 70 115 70 Q130 70 130 80 Q135 105 115 105 Q95 105 100 80 Z" stroke="#FFFDF8" strokeWidth="2" fill="#B5523B" />
  </svg>
);

/** Warli figures turning the pile */
export const WarliTurn: React.FC<WarliProps> = ({ className = '', size = 120 }) => (
  <svg
    viewBox="0 0 150 120"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{ width: size, height: (size * 120) / 150 }}
    className={className}
  >
    {/* Left figure bending forward with turning fork */}
    <circle cx="40" cy="35" r="9" stroke="#FFFDF8" strokeWidth="2.5" fill="#3A2218" />
    <polygon points="40,44 26,64 54,64" stroke="#FFFDF8" strokeWidth="2.5" fill="#3A2218" />
    <polygon points="40,84 26,64 54,64" stroke="#FFFDF8" strokeWidth="2.5" fill="#3A2218" />
    <path d="M30 84 L22 108" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" />
    <path d="M50 84 L58 108" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" />
    {/* Fork Arm */}
    <path d="M54 50 L75 60 L95 72" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" />
    {/* Fork Tines into Pile */}
    <line x1="95" y1="72" x2="105" y2="78" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" />
    <line x1="95" y1="72" x2="102" y2="85" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" />
    <line x1="95" y1="72" x2="90" y2="84" stroke="#FFFDF8" strokeWidth="2.5" strokeLinecap="round" />

    {/* Compost Mound with texture dots */}
    <path d="M70 108 Q105 75 140 108 Z" stroke="#FFFDF8" strokeWidth="2.5" fill="#B5523B" />
    <circle cx="95" cy="95" r="1.5" fill="#FFFDF8" />
    <circle cx="108" cy="90" r="1.5" fill="#FFFDF8" />
    <circle cx="120" cy="98" r="1.5" fill="#FFFDF8" />
  </svg>
);

/** The Squeeze Test (Wrung-out sponge feel) */
export const WarliSqueeze: React.FC<WarliProps> = ({ className = '', size = 120 }) => (
  <svg
    viewBox="0 0 130 110"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{ width: size, height: (size * 110) / 130 }}
    className={className}
  >
    {/* Hand Clenching Earth */}
    <rect x="35" y="40" width="45" height="30" rx="10" stroke="#FFFDF8" strokeWidth="2.5" fill="#3A2218" />
    {/* Fingers curving around handful */}
    <path d="M42 40 C42 30, 52 30, 52 40" stroke="#FFFDF8" strokeWidth="2.5" fill="none" />
    <path d="M54 40 C54 28, 64 28, 64 40" stroke="#FFFDF8" strokeWidth="2.5" fill="none" />
    <path d="M66 40 C66 30, 76 30, 76 40" stroke="#FFFDF8" strokeWidth="2.5" fill="none" />
    {/* Clump of Dark Moist Compost in fist */}
    <circle cx="78" cy="55" r="12" fill="#7A5236" stroke="#FFFDF8" strokeWidth="1.5" />
    {/* Exactly ONE clean droplet falling (55-60% optimal) */}
    <path d="M78 74 C78 74, 82 82, 82 85 C82 87.5, 80 89, 78 89 C76 89, 74 87.5, 74 85 C74 82, 78 74, 78 74 Z" fill="#3F6B3A" />
    {/* Text indicator */}
    <text x="65" y="104" fill="#3F6B3A" fontSize="10" fontWeight="bold" fontFamily="sans-serif">1 Droplet = Perfect</text>
  </svg>
);

/** Sprout growing from Matka */
export const WarliSprout: React.FC<WarliProps> = ({ className = '', size = 120 }) => (
  <svg
    viewBox="0 0 120 120"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{ width: size, height: size }}
    className={className}
  >
    {/* Sun above */}
    <circle cx="60" cy="22" r="8" stroke="#E0A92E" strokeWidth="2" fill="#F8E7B8" />
    <line x1="60" y1="8" x2="60" y2="12" stroke="#E0A92E" strokeWidth="2" strokeLinecap="round" />
    <line x1="60" y1="32" x2="60" y2="36" stroke="#E0A92E" strokeWidth="2" strokeLinecap="round" />
    <line x1="46" y1="22" x2="50" y2="22" stroke="#E0A92E" strokeWidth="2" strokeLinecap="round" />
    <line x1="70" y1="22" x2="74" y2="22" stroke="#E0A92E" strokeWidth="2" strokeLinecap="round" />

    {/* Central Growing Vine Stem */}
    <path d="M60 70 Q55 52 60 40" stroke="#3F6B3A" strokeWidth="3" strokeLinecap="round" />
    {/* Leaves branching */}
    <path d="M60 55 Q72 50 74 42 Q64 45 60 55 Z" fill="#3F6B3A" />
    <path d="M60 46 Q48 40 46 32 Q56 36 60 46 Z" fill="#52834C" />

    {/* Base Earthen Pot */}
    <path d="M40 70 Q40 64 60 64 Q80 64 80 70 Q86 100 60 100 Q34 100 40 70 Z" stroke="#FFFDF8" strokeWidth="2" fill="#B5523B" />
  </svg>
);
