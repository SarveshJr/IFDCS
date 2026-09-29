export type FireClass = 'Industrial Fire' | 'Gas Flare' | 'Mining Activity' | 'Wildfire' | 'Farm Burn';
export type Status = 'Confirmed' | 'Under Review' | 'Dismissed';

export interface Alert {
  id: string;
  lat: number;
  lng: number;
  className: FireClass;
  status: Status;
  frp: number; // Fire Radiative Power in MW
  facilityName?: string;
  timestamp: string;
  shapExplanation: string;
  landCover: string;
  isNewFacility?: boolean;
}

export const mockAlerts: Alert[] = [
  {
    id: 'ALT-101',
    lat: 22.34,
    lng: 82.72,
    className: 'Industrial Fire',
    status: 'Confirmed',
    frp: 340,
    facilityName: 'Korba Super Thermal Power Plant',
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
    shapExplanation: 'Flagged HIGH — 4x above normal FRP baseline, matches known thermal power plant footprint.',
    landCover: 'Built-up',
  },
  {
    id: 'ALT-102',
    lat: 23.76,
    lng: 86.43,
    className: 'Mining Activity',
    status: 'Dismissed',
    frp: 85,
    facilityName: 'Jharia Coalfield',
    timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
    shapExplanation: 'Consistent low-grade heat matching verified Bhuvan mining sub-class. No abnormal escalation.',
    landCover: 'Mining',
  },
  {
    id: 'ALT-103',
    lat: 22.8,
    lng: 70.13,
    className: 'Gas Flare',
    status: 'Under Review',
    frp: 120,
    facilityName: 'Jamnagar Refinery',
    timestamp: new Date(Date.now() - 10 * 60000).toISOString(),
    shapExplanation: 'Matches known flare stack location, but intensity is 2x historical rolling mean. Flagged for escalation.',
    landCover: 'Built-up',
  },
  {
    id: 'ALT-104',
    lat: 21.15,
    lng: 79.09,
    className: 'Wildfire',
    status: 'Confirmed',
    frp: 450,
    timestamp: new Date(Date.now() - 120 * 60000).toISOString(),
    shapExplanation: 'High FRP in forest area, no known industrial facility within 5km buffer.',
    landCover: 'Forest',
  },
  {
    id: 'ALT-105',
    lat: 19.98,
    lng: 73.75,
    className: 'Farm Burn',
    status: 'Dismissed',
    frp: 45,
    timestamp: new Date(Date.now() - 300 * 60000).toISOString(),
    shapExplanation: 'Seasonal low FRP matching cropland Bhuvan classification. Spread pattern indicates agricultural fire.',
    landCover: 'Cropland',
  },
  {
    id: 'ALT-106',
    lat: 18.52,
    lng: 73.85,
    className: 'Industrial Fire',
    status: 'Under Review',
    frp: 210,
    facilityName: 'Pune Auto Hub Plant 4',
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    shapExplanation: 'Insufficient baseline (Cold-Start Gate). FRP exceeds industry-average temporary baseline. Lower confidence.',
    landCover: 'Built-up',
    isNewFacility: true,
  }
];

export const generateFacilityHistory = (baseFrp: number, isAnomaly: boolean, isNew: boolean = false) => {
  const data = [];
  const days = isNew ? 10 : 90; // new facilities have less data
  const now = new Date();
  
  for (let i = days; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    // add some noise
    let frp = baseFrp + (Math.random() * 20 - 10);
    
    // create the anomaly on the last day
    if (i === 0 && isAnomaly) {
      frp = baseFrp * 3.5;
    }
    
    data.push({
      date: date.toISOString().split('T')[0],
      frp: Math.max(0, parseFloat(frp.toFixed(2))),
      rollingMean: isNew ? null : baseFrp,
    });
  }
  return data;
};
