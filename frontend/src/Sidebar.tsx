import React, { useState } from 'react';
import { AlertTriangle, MapPin, Activity, ShieldAlert, Target } from 'lucide-react';
import type { Alert, PredictionResult } from './App';

interface SidebarProps {
  activeAlerts: Alert[];
  predictionResult: PredictionResult | null;
}

const Sidebar: React.FC<SidebarProps> = ({ activeAlerts, predictionResult }) => {
  const [filterMode, setFilterMode] = useState<'all' | 'critical'>('all');

  // Compute filtered alerts dynamically on render (no strict state sync needed)
  const displayAlerts = activeAlerts
    .filter(a => filterMode === 'all' || a.risk_score > 0.95)
    .sort((a, b) => b.risk_score - a.risk_score);

  return (
    <aside className="w-96 bg-slate-900 border-r border-slate-800 flex flex-col h-full shadow-2xl relative z-20">
      <div className="p-5 border-b border-slate-800 bg-slate-950">
        <div className="flex items-center space-x-3 mb-2">
          <ShieldAlert className="text-blue-500" size={28} />
          <h1 className="text-xl font-bold uppercase tracking-widest text-slate-100">I4C Command Center</h1>
        </div>
        <p className="text-xs text-slate-400 font-mono">Proactive Cybercrime Intervention</p>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {predictionResult ? (
          <div className="p-5 animate-in slide-in-from-left-4 duration-300">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-blue-400 flex items-center">
                <Target size={18} className="mr-2" /> Traced Target
              </h2>
            </div>
            
            <div className="bg-slate-800 rounded-lg p-4 mb-6 border border-slate-700">
              <div className="text-xs text-slate-400 mb-1 font-mono">COMPLAINT NO</div>
              <div className="text-sm font-mono text-white mb-3">{predictionResult.complaint_details.ack_no}</div>
              
              <div className="text-xs text-slate-400 mb-1 font-mono">CATEGORY</div>
              <div className="text-sm text-yellow-400 mb-3">{predictionResult.complaint_details.crime_category}</div>
              
              <div className="text-xs text-slate-400 mb-1 font-mono">DEFRAUDED AMOUNT</div>
              <div className="text-sm text-red-400 font-semibold mb-3">
                ₹{predictionResult.complaint_details.defrauded_amount.toLocaleString()}
              </div>

              <div className="text-xs text-slate-400 mb-1 font-mono">MULE CHAIN HOPS</div>
              <div className="text-sm text-white">{predictionResult.mule_chain.length} transactions traced</div>
            </div>

            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center">
              <MapPin size={16} className="mr-2 text-red-500" /> Hotspot Forecast
            </h3>
            
            <div className="space-y-3">
              {predictionResult.predicted_hotspots.map((hotspot, idx) => (
                <div key={idx} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700 hover:border-red-500/50 transition-colors cursor-pointer">
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-mono text-sm text-white"># {hotspot.terminal_id}</div>
                    <div className="bg-red-900/50 text-red-400 text-xs px-2 py-1 rounded font-bold">
                      {(hotspot.risk_score * 100).toFixed(1)}% RISK
                    </div>
                  </div>
                  <div className="text-xs text-slate-400 mb-2">
                    Type: <span className="text-slate-200">{hotspot.terminal_type}</span>
                  </div>
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-emerald-400">Exp: ₹{Math.round(hotspot.expected_cashout_amount).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center">
                <Activity size={16} className="mr-2 text-red-500 animate-pulse" /> Live Threats
              </h2>
              <select 
                className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded p-1 outline-none"
                value={filterMode}
                onChange={(e) => setFilterMode(e.target.value as any)}
              >
                <option value="all">All Active</option>
                <option value="critical">Critical (&gt;95%)</option>
              </select>
            </div>

            <div className="space-y-3">
              {displayAlerts.length === 0 ? (
                <div className="text-center text-slate-500 py-10 text-sm">
                  No active threats detected.
                </div>
              ) : (
                displayAlerts.map((alert, idx) => (
                  <div key={idx} className="bg-slate-800/80 rounded-lg p-3 border-l-4 border-red-500 shadow-md">
                    <div className="flex justify-between items-center mb-1">
                      <div className="flex items-center text-red-400 font-bold text-xs uppercase">
                        <AlertTriangle size={14} className="mr-1" /> Dispatch Needed
                      </div>
                      <div className="text-slate-400 text-[10px] font-mono">
                        {new Date(alert.time_window_start).toLocaleTimeString()}
                      </div>
                    </div>
                    <div className="font-mono text-sm text-white mb-1">{alert.terminal_id}</div>
                    <div className="text-xs text-slate-400">Risk: {(alert.risk_score * 100).toFixed(0)}%</div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
