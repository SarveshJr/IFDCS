import { create } from 'zustand';
import type { Alert, FireClass } from '../data/mockData';
import { mockAlerts } from '../data/mockData';
import type { FirmsStats } from '../components/Map';

interface AppState {
  alerts: Alert[];
  selectedAlert: Alert | null;
  activeFilters: FireClass[];
  mapCenter: [number, number];
  mapZoom: number;
  firmsStats: FirmsStats;
  setSelectedAlert: (alert: Alert | null) => void;
  toggleFilter: (filter: FireClass) => void;
  setMapView: (center: [number, number], zoom: number) => void;
  setFirmsStats: (stats: FirmsStats) => void;
}

export const useStore = create<AppState>((set: any) => ({
  alerts: mockAlerts,
  selectedAlert: null,
  activeFilters: ['Industrial Fire', 'Gas Flare', 'Mining Activity', 'Wildfire', 'Farm Burn'],
  mapCenter: [22.0, 79.0],
  mapZoom: 5,
  firmsStats: {
    loading: true,
    totalHotspots: 0,
    highConfidence: 0,
    lastFetchTime: null,
    satellites: [],
    latestPass: null,
    frpMax: 0,
    frpAvg: 0,
    dayCount: 0,
    nightCount: 0,
  } as FirmsStats,
  
  setSelectedAlert: (alert: Alert | null) => set({ selectedAlert: alert }),
  
  toggleFilter: (filter: FireClass) => set((state: AppState) => ({
    activeFilters: state.activeFilters.includes(filter)
      ? state.activeFilters.filter((f: FireClass) => f !== filter)
      : [...state.activeFilters, filter]
  })),
  
  setMapView: (center: [number, number], zoom: number) => set({ mapCenter: center, mapZoom: zoom }),
  
  setFirmsStats: (stats: FirmsStats) => set({ firmsStats: stats }),
}));
