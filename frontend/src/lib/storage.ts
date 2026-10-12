import { Pile, PileLogEntry } from '../types';

const PILE_KEY = 'compostmitra_active_pile';
const GARDEN_KEY = 'compostmitra_garden_plants';

export const DEFAULT_PILE: Pile = {
  id: 'pile_default_1',
  name: 'Balcony Matka #1',
  size: 'matka',
  startDate: new Date(Date.now() - 12 * 86400000).toISOString(),
  dayCount: 12,
  maturityPercent: 42,
  state: 'healthy',
  temperatureC: 54, // active thermophilic zone
  lastTurnDay: 7,
  nextTurnDay: 14,
  totalWasteKg: 6.2,
  history: [
    {
      id: 'h1',
      date: new Date(Date.now() - 5 * 86400000).toLocaleDateString(),
      greensAddedCaddy: 1,
      brownsAddedHandfuls: 2,
      typeNote: 'Sabzi chilke + Chai patti',
      actionDone: 'Added 2 mutthi dry neem leaves',
    },
    {
      id: 'h2',
      date: new Date(Date.now() - 12 * 86400000).toLocaleDateString(),
      greensAddedCaddy: 1.5,
      brownsAddedHandfuls: 3,
      typeNote: 'Initial Matka Layering',
      actionDone: 'Base coco-peat bed + kitchen scraps',
    },
  ],
};

export function getActivePile(): Pile {
  try {
    const raw = localStorage.getItem(PILE_KEY);
    if (!raw) {
      saveActivePile(DEFAULT_PILE);
      return DEFAULT_PILE;
    }
    return JSON.parse(raw) as Pile;
  } catch {
    return DEFAULT_PILE;
  }
}

export function saveActivePile(pile: Pile): void {
  try {
    localStorage.setItem(PILE_KEY, JSON.stringify(pile));
  } catch (err) {
    console.error('Failed to save pile to localStorage', err);
  }
}

export function logWasteAdd(
  greensCaddy: number,
  brownsHandfuls: number,
  typeNote: string
): Pile {
  const current = getActivePile();
  const addedKg = Number((greensCaddy * 0.9 + brownsHandfuls * 0.05).toFixed(1));
  const newWasteKg = Number((current.totalWasteKg + addedKg).toFixed(1));

  const newEntry: PileLogEntry = {
    id: `log_${Date.now()}`,
    date: new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
    greensAddedCaddy: greensCaddy,
    brownsAddedHandfuls: brownsHandfuls,
    typeNote: typeNote || 'Kitchen Scraps',
    actionDone: `Added ${brownsHandfuls} mutthi browns`,
  };

  const updated: Pile = {
    ...current,
    totalWasteKg: newWasteKg,
    maturityPercent: Math.min(95, current.maturityPercent + 3),
    history: [newEntry, ...current.history],
  };

  saveActivePile(updated);
  return updated;
}

export function turnPileAction(): Pile {
  const current = getActivePile();
  const updated: Pile = {
    ...current,
    lastTurnDay: current.dayCount,
    nextTurnDay: current.dayCount + 7,
    maturityPercent: Math.min(100, current.maturityPercent + 8),
  };
  saveActivePile(updated);
  return updated;
}

export function resetPile(name: string, size: Pile['size']): Pile {
  const newPile: Pile = {
    id: `pile_${Date.now()}`,
    name: name || 'Naya Matka',
    size: size,
    startDate: new Date().toISOString(),
    dayCount: 1,
    maturityPercent: 5,
    state: 'healthy',
    temperatureC: 28,
    lastTurnDay: 0,
    nextTurnDay: 7,
    totalWasteKg: 0,
    history: [],
  };
  saveActivePile(newPile);
  return newPile;
}
