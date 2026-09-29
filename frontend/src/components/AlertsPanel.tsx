import { useStore } from '../store/useStore';
import { formatDistanceToNow } from 'date-fns';
import { ShieldAlert, AlertTriangle, CheckCircle2, Flame, BrainCircuit, XCircle } from 'lucide-react';
import { clsx } from 'clsx';
import type { Alert } from '../data/mockData';

const getStatusIcon = (status: Alert['status']) => {
  switch (status) {
    case 'Confirmed': return <ShieldAlert className="w-4 h-4 text-red-500" />;
    case 'Under Review': return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    case 'Dismissed': return <CheckCircle2 className="w-4 h-4 text-gray-500" />;
  }
};

const getClassColor = (cls: Alert['className']) => {
  switch (cls) {
    case 'Industrial Fire': return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'Gas Flare': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'Mining Activity': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'Wildfire': return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'Farm Burn': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
  }
};

export const AlertsPanel = () => {
  const { alerts, activeFilters, setSelectedAlert, setMapView } = useStore();

  const filteredAlerts = alerts.filter((a: Alert) => activeFilters.includes(a.className))
    .sort((a: Alert, b: Alert) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  const handleAlertClick = (alert: Alert) => {
    setSelectedAlert(alert);
    setMapView([alert.lat, alert.lng], 12);
  };

  return (
    <div className="w-96 bg-[#1a1a1a] border-l border-gray-800 flex flex-col z-20 shadow-xl overflow-hidden">
      <div className="p-5 border-b border-gray-800 flex items-center justify-between bg-[#1e1e1e]">
        <h2 className="font-semibold text-gray-200 flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-red-500" />
          Active Intelligence
        </h2>
        <span className="bg-red-500/20 text-red-400 text-xs px-2 py-1 rounded-full border border-red-500/30">
          {filteredAlerts.length} Events
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {filteredAlerts.map((alert: Alert) => (
          <div 
            key={alert.id}
            onClick={() => handleAlertClick(alert)}
            className={clsx(
              "p-4 rounded-lg border cursor-pointer transition-all",
              alert.status === 'Dismissed' 
                ? "bg-[#181818] border-gray-800 hover:border-gray-700 opacity-70"
                : "bg-[#222] border-gray-700 hover:border-gray-600 hover:shadow-lg hover:shadow-black/50"
            )}
          >
            <div className="flex justify-between items-start mb-3">
              <div className="flex items-center gap-2">
                {getStatusIcon(alert.status)}
                <span className="text-xs font-medium text-gray-400">
                  {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                </span>
              </div>
              <span className={clsx("text-[10px] px-2 py-0.5 rounded border uppercase tracking-wider font-semibold", getClassColor(alert.className))}>
                {alert.className}
              </span>
            </div>

            <div className="mb-3">
              <h3 className="font-medium text-gray-200 text-sm">
                {alert.facilityName || `Unknown Location (${alert.lat.toFixed(2)}, ${alert.lng.toFixed(2)})`}
              </h3>
              {alert.isNewFacility && (
                <span className="inline-flex items-center gap-1 text-[10px] text-blue-400 bg-blue-400/10 border border-blue-400/20 px-1.5 py-0.5 rounded mt-1">
                  <AlertTriangle className="w-3 h-3" />
                  Cold-Start Gate
                </span>
              )}
            </div>

            <div className="flex items-center gap-4 mb-4">
              <div className="flex items-center gap-1.5">
                <Flame className="w-4 h-4 text-orange-500" />
                <span className="text-xl font-bold text-gray-100">{alert.frp}</span>
                <span className="text-xs text-gray-500">MW</span>
              </div>
              <div className="h-6 w-px bg-gray-700"></div>
              <div className="text-xs text-gray-400 flex flex-col">
                <span className="uppercase text-[9px] tracking-wider text-gray-600">Land Cover</span>
                {alert.landCover}
              </div>
            </div>

            <div className="bg-[#1a1a1a] p-3 rounded border border-gray-800/50 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-1 h-full bg-blue-500/50"></div>
              <div className="flex gap-2 items-start">
                <BrainCircuit className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <p className="text-xs text-gray-400 leading-relaxed italic">
                  <span className="text-blue-400/80 font-medium not-italic mr-1">SHAP:</span> 
                  {alert.shapExplanation}
                </p>
              </div>
            </div>
          </div>
        ))}
        {filteredAlerts.length === 0 && (
          <div className="text-center p-8 text-gray-600 flex flex-col items-center gap-3">
            <XCircle className="w-8 h-8 opacity-50" />
            <p className="text-sm">No events match the current filters.</p>
          </div>
        )}
      </div>
    </div>
  );
};
