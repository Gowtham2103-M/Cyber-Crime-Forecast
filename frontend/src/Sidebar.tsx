import React, { useState } from 'react';
import { AlertTriangle, MapPin, Activity, ShieldAlert, Target, ArrowLeft } from 'lucide-react';
import type { Alert, PredictionResult } from './App';

interface SidebarProps {
  activeAlerts: Alert[];
  predictionResult: PredictionResult | null;
  onTriangulate?: () => void;
  isTriangulating?: boolean;
  onClearPrediction?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeAlerts, predictionResult, onTriangulate, isTriangulating, onClearPrediction }) => {
  const [filterMode, setFilterMode] = useState<'all' | 'critical'>('all');

  // Compute filtered alerts dynamically on render (no strict state sync needed)
  const displayAlerts = activeAlerts
    .filter(a => filterMode === 'all' || a.risk_score > 0.95)
    .sort((a, b) => b.risk_score - a.risk_score);

  return (
    <aside className="w-[420px] bg-slate-950/95 backdrop-blur-xl border-r border-white/5 flex flex-col h-full shadow-[0_0_50px_rgba(0,0,0,0.5)] relative z-20">
      <div className="p-6 border-b border-white/5 bg-gradient-to-b from-slate-900/80 to-transparent">
        <div className="flex items-center space-x-3 mb-1">
          <ShieldAlert className="text-blue-500" size={24} />
          <h1 className="text-lg font-black uppercase tracking-[0.15em] bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
            I4C Command Center
          </h1>
        </div>
        <p className="text-[10px] text-slate-500 font-mono tracking-widest pl-9">PROACTIVE CYBERCRIME INTERVENTION</p>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {predictionResult ? (
          <div className="p-5 animate-in slide-in-from-left-4 duration-300">
            <div className="flex items-center mb-6 border-b border-white/5 pb-4">
              <button 
                onClick={onClearPrediction}
                className="mr-3 p-1.5 rounded-lg bg-slate-900 border border-white/10 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                title="Back to Live Threats"
              >
                <ArrowLeft size={16} />
              </button>
              <h2 className="text-sm font-black text-blue-400 uppercase tracking-widest flex items-center">
                <Target size={16} className="mr-2" /> Traced Target
              </h2>
            </div>
            
            <div className="bg-slate-900/50 backdrop-blur-md rounded-xl p-5 mb-6 border border-white/5 shadow-inner">
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div>
                  <div className="text-[10px] text-slate-500 mb-1 font-mono tracking-widest">COMPLAINT NO</div>
                  <div className="text-xs font-mono text-slate-200 bg-slate-950/50 px-2 py-1 rounded border border-white/5 inline-block">{predictionResult.complaint_details.ack_no}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 mb-1 font-mono tracking-widest">CATEGORY</div>
                  <div className="text-[10px] text-yellow-400 font-semibold bg-yellow-400/10 px-2 py-1.5 rounded border border-yellow-500/20 inline-block truncate max-w-full" title={predictionResult.complaint_details.crime_category}>
                    {predictionResult.complaint_details.crime_category.split('-')[0]}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 mb-1 font-mono tracking-widest">DEFRAUDED AMOUNT</div>
                  <div className="text-sm text-red-400 font-bold bg-red-950/30 px-2 py-1 rounded border border-red-500/10 inline-block">
                    ₹{predictionResult.complaint_details.defrauded_amount.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 mb-1 font-mono tracking-widest">MULE CHAIN HOPS</div>
                  <div className="text-sm text-blue-400 font-bold bg-blue-950/30 px-2 py-1 rounded border border-blue-500/10 inline-block">
                    {predictionResult.mule_chain.length} transactions
                  </div>
                </div>
              </div>
              
              <button 
                onClick={onTriangulate}
                disabled={isTriangulating}
                className="w-full bg-gradient-to-r from-red-900 to-rose-700 hover:from-red-800 hover:to-rose-600 text-white text-xs font-bold tracking-widest py-3 px-4 rounded-lg border border-red-500/30 shadow-[0_0_15px_rgba(225,29,72,0.2)] hover:shadow-[0_0_20px_rgba(225,29,72,0.4)] transition-all disabled:opacity-50 flex items-center justify-center uppercase"
              >
                <Target size={16} className="mr-2" />
                {isTriangulating ? 'PROFILING GEOGRAPHY...' : 'TRIANGULATE HIDEOUT'}
              </button>
            </div>

            {predictionResult.flagged_nodes && predictionResult.flagged_nodes.length > 0 && (
              <div className="mb-8">
                <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-3 flex items-center">
                  <ShieldAlert size={14} className="mr-2 text-orange-500" /> Flagged Network Nodes
                </h3>
                <div className="space-y-2">
                  {predictionResult.flagged_nodes.map((node: any, idx: number) => (
                    <div key={idx} className="bg-slate-900/60 rounded-lg border border-orange-500/20 p-3 hover:border-orange-500/40 transition-colors">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-mono text-[11px] text-slate-200 break-all pr-2">Acc: {node.account.slice(0, 14)}...</span>
                        <span className={`text-[9px] uppercase font-bold px-2 py-0.5 rounded-full border ${
                          node.risk_level === 'Critical' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 
                          node.risk_level === 'High' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                        }`}>
                          {node.risk_level}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 mb-2 leading-relaxed">{node.reason}</div>
                      <div className="flex space-x-3 text-[9px] font-mono text-slate-500 bg-slate-950/50 p-1.5 rounded inline-flex">
                        <span>IN: <span className="text-slate-300">{node.in_degree}</span></span>
                        <span>OUT: <span className="text-slate-300">{node.out_degree}</span></span>
                        <span>PTR: <span className="text-slate-300">{node.pass_through_ratio.toFixed(2)}</span></span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-3 flex items-center">
              <MapPin size={14} className="mr-2 text-rose-500" /> Hotspot Forecast
            </h3>
            
            <div className="space-y-3">
              {predictionResult.predicted_hotspots.map((hotspot, idx) => (
                <div key={idx} className="bg-slate-900/60 rounded-lg p-3 border border-slate-800 hover:border-rose-500/30 transition-all cursor-pointer shadow-sm hover:shadow-[0_0_15px_rgba(225,29,72,0.1)] group">
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-mono text-sm text-slate-200 group-hover:text-white transition-colors"># {hotspot.terminal_id}</div>
                    <div className="bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider">
                      {(hotspot.risk_score * 100).toFixed(1)}% RISK
                    </div>
                  </div>
                  <div className="text-[11px] text-slate-500 mb-2 tracking-wide uppercase">
                    Type: <span className="text-slate-300 font-medium">{hotspot.terminal_type}</span>
                  </div>
                  <div className="flex justify-between items-center text-[11px] font-mono">
                    <span className="text-emerald-400/90 font-semibold bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-500/10">Exp: ₹{Math.round(hotspot.expected_cashout_amount).toLocaleString()}</span>
                    {hotspot.eta_minutes && (
                      <span className="text-orange-400/90 font-semibold bg-orange-950/30 px-2 py-0.5 rounded border border-orange-500/10 animate-pulse">
                        ETA: ~{hotspot.eta_minutes} mins
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-5">
            <div className="flex justify-between items-center mb-6 border-b border-white/5 pb-4">
              <h2 className="text-[11px] font-black text-slate-300 uppercase tracking-widest flex items-center">
                <Activity size={14} className="mr-2 text-rose-500 animate-pulse" /> Live Threats
              </h2>
              <select 
                className="bg-slate-900/50 border border-white/10 text-[10px] text-slate-300 rounded-md px-2 py-1 outline-none uppercase tracking-wider cursor-pointer focus:ring-1 focus:ring-rose-500/50"
                value={filterMode}
                onChange={(e) => setFilterMode(e.target.value as any)}
              >
                <option value="all">All Active</option>
                <option value="critical">Critical (&gt;95%)</option>
              </select>
            </div>

            <div className="space-y-4">
              {displayAlerts.length === 0 ? (
                <div className="text-center text-slate-500 py-10 text-sm">
                  No active threats detected.
                </div>
              ) : (
                displayAlerts.map((alert, idx) => (
                  <div key={idx} className="bg-slate-900/40 rounded-xl p-4 border border-white/5 border-l-2 border-l-rose-500 hover:bg-slate-900/60 transition-all shadow-sm">
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center text-rose-500/90 font-black text-[9px] uppercase tracking-widest bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                        <AlertTriangle size={10} className="mr-1" /> Dispatch Needed
                      </div>
                      <div className="text-orange-400/90 text-[10px] font-mono tracking-wider font-semibold bg-orange-500/10 px-2 py-0.5 rounded border border-orange-500/20">
                        ETA: {alert.expected_cashout_time ? new Date(alert.expected_cashout_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : new Date(alert.time_window_start).toLocaleTimeString()}
                      </div>
                    </div>
                    <div className="flex justify-between items-center mb-1">
                      <div className="font-mono text-[13px] text-slate-200">{alert.terminal_id}</div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        Risk: <span className="text-rose-400 font-bold">{(alert.risk_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    
                    {(alert as any).associated_acks && (alert as any).associated_acks.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-white/5">
                        <div className="text-[9px] text-slate-500 mb-2 font-black uppercase tracking-widest">Associated Cases:</div>
                        <div className="flex flex-wrap gap-1.5">
                          {(alert as any).associated_acks.map((ack: string) => (
                            <span 
                              key={ack} 
                              className="text-[9px] font-mono text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full cursor-pointer hover:bg-blue-500/20 hover:text-blue-300 hover:border-blue-500/40 transition-all shadow-sm"
                              onClick={() => {
                                if ((window as any).directSearch) {
                                  (window as any).directSearch(ack);
                                }
                              }}
                            >
                              {ack}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
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
