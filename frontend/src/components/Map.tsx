import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, useMap, CircleMarker, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useStore } from '../store/useStore';
import { fetchFirmsData, type FirmsHotspot } from '../data/firmsApi';

// Color a FIRMS hotspot by its FRP intensity
const getFirmsColor = (frp: number): string => {
  if (frp >= 100) return '#ef4444';      // red — high intensity
  if (frp >= 30)  return '#f97316';       // orange — medium
  if (frp >= 10)  return '#eab308';       // yellow — low-medium
  return '#f59e0b';                       // amber — low
};

const getFirmsRadius = (frp: number): number => {
  if (frp >= 200) return 6;
  if (frp >= 50)  return 4;
  return 3;
};

const MapController = () => {
  const { mapCenter, mapZoom } = useStore();
  const map = useMap();
  
  useEffect(() => {
    map.flyTo(mapCenter, mapZoom, { duration: 1.5 });
  }, [mapCenter, mapZoom, map]);
  
  return null;
};

export interface FirmsStats {
  loading: boolean;
  totalHotspots: number;
  highConfidence: number;
  lastFetchTime: string | null;
  satellites: { name: string; count: number }[];
  latestPass: string | null;
  frpMax: number;
  frpAvg: number;
  dayCount: number;
  nightCount: number;
}

export const MapView = () => {
  const { setFirmsStats } = useStore();
  const [firmsHotspots, setFirmsHotspots] = useState<FirmsHotspot[]>([]);

  // Fetch real FIRMS data on mount
  useEffect(() => {
    setFirmsStats({
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
    });

    fetchFirmsData(2).then((data: FirmsHotspot[]) => {
      setFirmsHotspots(data);
      
      // Compute statistics for the sidebar
      const satMap = new Map<string, number>();
      let highConf = 0;
      let frpMax = 0;
      let frpSum = 0;
      let dayCount = 0;
      let nightCount = 0;
      let latestDate = '';
      let latestTime = '';

      for (const hs of data) {
        // Satellite counts
        const satName = hs.satellite || 'Unknown';
        satMap.set(satName, (satMap.get(satName) || 0) + 1);

        // Confidence
        if (hs.confidence === 'h' || hs.confidence === 'high') highConf++;

        // FRP
        if (hs.frp > frpMax) frpMax = hs.frp;
        frpSum += hs.frp;

        // Day/Night
        if (hs.daynight === 'D') dayCount++;
        else nightCount++;

        // Latest pass
        if (hs.acq_date > latestDate || (hs.acq_date === latestDate && hs.acq_time > latestTime)) {
          latestDate = hs.acq_date;
          latestTime = hs.acq_time;
        }
      }

      const satellites = Array.from(satMap.entries())
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count);

      const latestPass = latestDate
        ? `${latestDate} ${latestTime.padStart(4, '0').slice(0, 2)}:${latestTime.padStart(4, '0').slice(2)} UTC`
        : null;

      setFirmsStats({
        loading: false,
        totalHotspots: data.length,
        highConfidence: highConf,
        lastFetchTime: new Date().toLocaleTimeString(),
        satellites,
        latestPass,
        frpMax,
        frpAvg: data.length > 0 ? parseFloat((frpSum / data.length).toFixed(1)) : 0,
        dayCount,
        nightCount,
      });
    });
  }, [setFirmsStats]);

  const indiaBounds: L.LatLngBoundsExpression = [
    [5.0, 60.0],
    [38.0, 100.0],
  ];

  return (
    <div className="absolute inset-0 z-0">
      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.8; }
          100% { transform: scale(1); opacity: 1; }
        }
        .leaflet-popup-content-wrapper {
          background-color: #1a1a1a;
          color: white;
          border: 1px solid #333;
          border-radius: 0.5rem;
        }
        .leaflet-popup-tip {
          background-color: #1a1a1a;
          border: 1px solid #333;
        }
      `}</style>

      <MapContainer 
        center={[22.0, 79.0]} 
        zoom={5} 
        minZoom={4}
        maxZoom={14}
        maxBounds={indiaBounds}
        maxBoundsViscosity={1.0}
        style={{ width: '100%', height: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapController />
        
        {/* Real NASA FIRMS hotspots */}
        {firmsHotspots.map((hs: FirmsHotspot, idx: number) => (
          <CircleMarker
            key={`firms-${idx}`}
            center={[hs.latitude, hs.longitude]}
            radius={getFirmsRadius(hs.frp)}
            pathOptions={{
              color: getFirmsColor(hs.frp),
              fillColor: getFirmsColor(hs.frp),
              fillOpacity: 0.7,
              weight: 1,
            }}
          >
            <Tooltip direction="top" offset={[0, -5]}>
              <div style={{ color: '#fff', background: '#1a1a1a', padding: '6px 10px', borderRadius: '6px', fontSize: '11px', border: '1px solid #333' }}>
                <div style={{ fontWeight: 'bold', marginBottom: '3px' }}>FIRMS Hotspot</div>
                <div>FRP: <span style={{ color: '#f97316', fontWeight: 'bold' }}>{hs.frp} MW</span></div>
                <div>Brightness: {hs.brightness.toFixed(1)}K</div>
                <div>Confidence: {hs.confidence}</div>
                <div style={{ color: '#888', marginTop: '2px' }}>{hs.acq_date} {hs.acq_time} · {hs.satellite}</div>
              </div>
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
};
