import { useStore } from '../store/useStore';
import { Satellite, Radio, Flame, Sun, Moon, TrendingUp, Clock, Activity, Loader2, Zap } from 'lucide-react';

export const Sidebar = () => {
  const { firmsStats } = useStore();

  return (
    <aside className="w-72 bg-[#1a1a1a] border-r border-gray-800 flex flex-col z-20 shadow-xl">
      {/* Header */}
      <div className="p-5 border-b border-gray-800 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
          <Activity className="w-6 h-6 text-orange-500" />
        </div>
        <div>
          <h2 className="font-bold text-white tracking-wider">IFDCS</h2>
          <p className="text-xs text-gray-500">Live Monitoring</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {/* Connection Status */}
        <div className="p-5 border-b border-gray-800">
          <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-3">
            Data Pipeline Status
          </h3>
          <div className="flex items-center gap-2 mb-2">
            {firmsStats.loading ? (
              <>
                <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />
                <span className="text-sm text-yellow-400">Fetching satellite data…</span>
              </>
            ) : (
              <>
                <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
                <span className="text-sm text-green-400">Connected to NASA FIRMS</span>
              </>
            )}
          </div>
          {firmsStats.lastFetchTime && (
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
              <Clock className="w-3 h-3" />
              <span>Last sync: {firmsStats.lastFetchTime}</span>
            </div>
          )}
        </div>

        {/* Satellite Sources */}
        <div className="p-5 border-b border-gray-800">
          <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
            <Radio className="w-3 h-3" />
            Satellite Sources
          </h3>
          {firmsStats.loading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <div key={i} className="h-10 bg-[#222] rounded-md animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {firmsStats.satellites.map((sat) => (
                <div key={sat.name} className="flex items-center justify-between bg-[#222] rounded-md px-3 py-2.5 border border-gray-800">
                  <div className="flex items-center gap-2">
                    <Satellite className="w-4 h-4 text-blue-400" />
                    <span className="text-sm text-gray-200">{sat.name}</span>
                  </div>
                  <span className="text-xs font-mono text-orange-400 bg-orange-400/10 px-2 py-0.5 rounded">
                    {sat.count.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
          {firmsStats.latestPass && (
            <div className="mt-3 text-[10px] text-gray-500 flex items-center gap-1.5">
              <Clock className="w-3 h-3" />
              Latest pass: <span className="text-gray-400 font-mono">{firmsStats.latestPass}</span>
            </div>
          )}
        </div>

        {/* Live Stats */}
        <div className="p-5 border-b border-gray-800">
          <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
            <TrendingUp className="w-3 h-3" />
            Live Statistics (48h)
          </h3>
          
          <div className="grid grid-cols-2 gap-2">
            {/* Total Hotspots */}
            <div className="bg-[#222] rounded-md p-3 border border-gray-800">
              <div className="flex items-center gap-1.5 mb-1">
                <Flame className="w-3 h-3 text-red-500" />
                <span className="text-[10px] text-gray-500 uppercase">Hotspots</span>
              </div>
              <span className="text-xl font-bold text-gray-100 font-mono">
                {firmsStats.loading ? '—' : firmsStats.totalHotspots.toLocaleString()}
              </span>
            </div>

            {/* High Confidence */}
            <div className="bg-[#222] rounded-md p-3 border border-gray-800">
              <div className="flex items-center gap-1.5 mb-1">
                <Zap className="w-3 h-3 text-yellow-500" />
                <span className="text-[10px] text-gray-500 uppercase">High Conf.</span>
              </div>
              <span className="text-xl font-bold text-gray-100 font-mono">
                {firmsStats.loading ? '—' : firmsStats.highConfidence.toLocaleString()}
              </span>
            </div>

            {/* Peak FRP */}
            <div className="bg-[#222] rounded-md p-3 border border-gray-800">
              <div className="flex items-center gap-1.5 mb-1">
                <TrendingUp className="w-3 h-3 text-orange-500" />
                <span className="text-[10px] text-gray-500 uppercase">Peak FRP</span>
              </div>
              <div>
                <span className="text-xl font-bold text-orange-400 font-mono">
                  {firmsStats.loading ? '—' : firmsStats.frpMax.toFixed(1)}
                </span>
                <span className="text-[10px] text-gray-500 ml-1">MW</span>
              </div>
            </div>

            {/* Avg FRP */}
            <div className="bg-[#222] rounded-md p-3 border border-gray-800">
              <div className="flex items-center gap-1.5 mb-1">
                <Activity className="w-3 h-3 text-blue-400" />
                <span className="text-[10px] text-gray-500 uppercase">Avg FRP</span>
              </div>
              <div>
                <span className="text-xl font-bold text-blue-400 font-mono">
                  {firmsStats.loading ? '—' : firmsStats.frpAvg}
                </span>
                <span className="text-[10px] text-gray-500 ml-1">MW</span>
              </div>
            </div>
          </div>
        </div>

        {/* Day / Night Split */}
        <div className="p-5">
          <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-3">
            Detection Window
          </h3>
          {!firmsStats.loading && firmsStats.totalHotspots > 0 ? (
            <>
              <div className="flex items-center gap-3 mb-2">
                <Sun className="w-4 h-4 text-yellow-400" />
                <div className="flex-1">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">Day detections</span>
                    <span className="text-gray-300 font-mono">{firmsStats.dayCount.toLocaleString()}</span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-yellow-500 rounded-full transition-all duration-1000"
                      style={{ width: `${(firmsStats.dayCount / firmsStats.totalHotspots) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Moon className="w-4 h-4 text-blue-400" />
                <div className="flex-1">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">Night detections</span>
                    <span className="text-gray-300 font-mono">{firmsStats.nightCount.toLocaleString()}</span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all duration-1000"
                      style={{ width: `${(firmsStats.nightCount / firmsStats.totalHotspots) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-xs text-gray-600 italic">Waiting for data…</div>
          )}
        </div>
      </div>
      
      <div className="p-4 border-t border-gray-800 text-xs text-gray-600 text-center">
        Powered by INSAT & FIRMS
      </div>
    </aside>
  );
};
