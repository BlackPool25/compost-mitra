export type PileSize = 'matka' | 'bucket' | 'drum' | 'bed';

export type PileState = 'healthy' | 'needs_browns' | 'too_wet' | 'act_now' | 'cold_sleeping';

export type Mitratone = 'calm' | 'sleepy' | 'sweating' | 'sniffing' | 'proud' | 'resting';

export interface Pile {
  id: string;
  name: string;
  size: PileSize;
  startDate: string; // ISO date string
  dayCount: number;
  maturityPercent: number; // 0 - 100
  state: PileState;
  temperatureC?: number;
  lastTurnDay?: number;
  nextTurnDay: number;
  totalWasteKg: number;
  history: PileLogEntry[];
}

export interface PileLogEntry {
  id: string;
  date: string;
  greensAddedCaddy: number;
  brownsAddedHandfuls: number;
  typeNote: string;
  actionDone: string;
}

export interface KitchenItem {
  id: string;
  name: string;
  hinglishName: string;
  category: 'green' | 'brown' | 'blocked';
  carbonRatio: number; // C:N
  moisturePct: number;
  unit: 'caddy' | 'plate' | 'filter' | 'handful';
  unitLabel: string;
  explanationIfBlocked?: string;
}

export interface DoctorSymptom {
  id: string;
  category: 'smell' | 'pests' | 'temp' | 'moisture';
  title: string;
  hinglishTitle: string;
  description: string;
  mitraMessage: string;
  rootCause: string;
  immediateAction: string;
  howToSteps: string[];
  preventNext: string;
}

export interface PlantProfile {
  id: string;
  name: string;
  hinglishName: string;
  family: string;
  containerSize: string;
  sunlightHours: number;
  compostPerMonthHandfuls: number;
  stageNote: string;
  pCapWarning?: string;
}

export interface PlantGrowthEntry {
  id: string;
  plantId: string;
  date: string;
  stage: 'seedling' | 'vegetative' | 'flowering' | 'fruiting' | 'harvest';
  vigor: 'thriving' | 'moderate' | 'struggling';
  notes: string;
}
