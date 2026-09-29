const FIRMS_API_KEY = '8551cc2bf81f8958c6321637e0900067';

export interface FirmsHotspot {
  latitude: number;
  longitude: number;
  brightness: number;
  scan: number;
  track: number;
  acq_date: string;
  acq_time: string;
  satellite: string;
  confidence: string;
  frp: number;
  daynight: string;
}

/**
 * Fetch active fire data from NASA FIRMS for the India region (last N days).
 * Uses the area endpoint with India's bounding box, proxied through Vite to avoid CORS.
 * Bounding box: west=68, south=6, east=98, north=37
 */
export async function fetchFirmsData(days: number = 1): Promise<FirmsHotspot[]> {
  // Use the area/csv endpoint (country endpoint returns 400)
  // Routed through Vite proxy (/firms-api -> https://firms.modaps.eosdis.nasa.gov)
  const url = `/firms-api/api/area/csv/${FIRMS_API_KEY}/VIIRS_SNPP_NRT/68,6,98,37/${days}`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      console.error('FIRMS API error:', response.status, response.statusText);
      return [];
    }
    
    const csvText = await response.text();
    return parseCsv(csvText);
  } catch (error) {
    console.error('Failed to fetch FIRMS data:', error);
    return [];
  }
}

function parseCsv(csv: string): FirmsHotspot[] {
  const lines = csv.trim().split('\n');
  if (lines.length < 2) return [];
  
  const headers = lines[0].split(',');
  const latIdx = headers.indexOf('latitude');
  const lngIdx = headers.indexOf('longitude');
  const brightnessIdx = headers.indexOf('bright_ti4');
  const scanIdx = headers.indexOf('scan');
  const trackIdx = headers.indexOf('track');
  const dateIdx = headers.indexOf('acq_date');
  const timeIdx = headers.indexOf('acq_time');
  const satIdx = headers.indexOf('satellite');
  const confIdx = headers.indexOf('confidence');
  const frpIdx = headers.indexOf('frp');
  const dnIdx = headers.indexOf('daynight');
  
  const hotspots: FirmsHotspot[] = [];
  
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',');
    if (cols.length < headers.length) continue;
    
    hotspots.push({
      latitude: parseFloat(cols[latIdx]),
      longitude: parseFloat(cols[lngIdx]),
      brightness: parseFloat(cols[brightnessIdx]) || 0,
      scan: parseFloat(cols[scanIdx]) || 0,
      track: parseFloat(cols[trackIdx]) || 0,
      acq_date: cols[dateIdx] || '',
      acq_time: cols[timeIdx] || '',
      satellite: cols[satIdx] || '',
      confidence: cols[confIdx] || '',
      frp: parseFloat(cols[frpIdx]) || 0,
      daynight: cols[dnIdx] || '',
    });
  }
  
  return hotspots;
}
