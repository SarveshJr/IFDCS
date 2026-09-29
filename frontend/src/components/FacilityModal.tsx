import { useMemo } from 'react';
import { useStore } from '../store/useStore';
import { generateFacilityHistory } from '../data/mockData';
import { X, TrendingUp, MapPin, Satellite, Info } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export const FacilityModal = () => {
  const { selectedAlert, setSelectedAlert } = useStore();

  const historyData = useMemo(() => {
    if (!selectedAlert) return [];
    return generateFacilityHistory(
      selectedAlert.frp / (selectedAlert.className === 'Industrial Fire' ? 3.5 : 1.2), 
      selectedAlert.className === 'Industrial Fire' || selectedAlert.className === 'Gas Flare',
      selectedAlert.isNewFacility
    );
  }, [selectedAlert]);

  if (!selectedAlert) return null;

  return (
    <div className="absolute bottom-6 left-72 right-[400px] bg-[#1a1a1a] border border-gray-800 rounded-xl shadow-2xl z-30 flex flex-col max-h-[400px] overflow-hidden animate-in slide-in-from-bottom-10 fade-in duration-300">
      <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-[#1e1e1e]">
        <div>
          <h2 className="text-lg font-bold text-gray-100 flex items-center gap-2">
            {selectedAlert.facilityName || 'Unregistered Location'}
            {selectedAlert.isNewFacility && (
              <span className="text-[10px] bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded border border-blue-500/30 font-medium">
                New Facility
              </span>
            )}
          </h2>
          <div className="flex items-center gap-4 text-xs text-gray-500 mt-1">
            <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {selectedAlert.lat.toFixed(4)}, {selectedAlert.lng.toFixed(4)}</span>
            <span className="flex items-center gap-1"><Info className="w-3 h-3" /> {selectedAlert.landCover}</span>
          </div>
        </div>
        <button 
          onClick={() => setSelectedAlert(null)}
          className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 flex gap-6 custom-scrollbar">
        {/* Chart Section */}
        <div className="flex-1 flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-gray-400" />
              Thermal Signature Baseline (FRP MW)
            </h3>
            {selectedAlert.isNewFacility && (
              <span className="text-xs text-blue-400 italic">Insufficient baseline (using industry avg)</span>
            )}
          </div>
          
          <div className="flex-1 min-h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis dataKey="date" stroke="#666" tick={{ fill: '#666', fontSize: 10 }} tickMargin={10} minTickGap={30} />
                <YAxis stroke="#666" tick={{ fill: '#666', fontSize: 10 }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e1e1e', borderColor: '#333', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                {!selectedAlert.isNewFacility && (
                  <ReferenceLine y={historyData[0]?.rollingMean ?? undefined} stroke="#fb923c" strokeDasharray="3 3" label={{ position: 'top', value: 'Baseline Mean', fill: '#fb923c', fontSize: 10 }} />
                )}
                <Line type="monotone" dataKey="frp" stroke="#ef4444" strokeWidth={2} dot={false} activeDot={{ r: 6, fill: '#ef4444' }} name="Observed FRP" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Optical Confirmation Section */}
        <div className="w-64 flex flex-col border-l border-gray-800 pl-6">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2 mb-4">
            <Satellite className="w-4 h-4 text-gray-400" />
            Optical Confirmation
          </h3>
          
          <div className="flex-1 bg-black rounded-lg border border-gray-700 relative overflow-hidden group">
            {/* Simulated Satellite Image Placeholder */}
            <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1614027164847-1b28cfe1df60?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80')] bg-cover bg-center opacity-60 mix-blend-luminosity"></div>
            <div className="absolute inset-0 bg-gradient-to-t from-[#1a1a1a] to-transparent opacity-80"></div>
            
            {/* Heat overlay simulation */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-red-500/40 blur-xl rounded-full"></div>
            
            <div className="absolute bottom-3 left-3 right-3 flex flex-col gap-1">
              <span className="text-[10px] font-mono text-gray-400 bg-black/60 px-2 py-1 rounded w-fit backdrop-blur-sm">
                Sentinel-2 SWIR
              </span>
              <span className="text-[9px] text-gray-500 flex justify-between">
                <span>Async Fetch</span>
                <span className="text-green-400">Success</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
