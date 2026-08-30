import React, { useState, useEffect } from 'react';
import axios from 'axios';
import MapComponent from './MapComponent';
import Sidebar from './Sidebar';
import { Search, Target } from 'lucide-react';

export interface Alert {
  terminal_id: string;
  latitude: number;
  longitude: number;
  terminal_type: string;
  risk_score: number;
  time_window_start: string;
  time_window_end: string;
  expected_cashout_time?: string;
  eta_minutes?: number;
  expected_cashout_amount: number;
  explanation?: {
    baseline_spatial_pct: number;
    recent_activity_pct: number;
    network_link_pct: number;
    details: string[];
  };
}

export interface FlaggedNode {
  account: string;
  in_degree: number;
  out_degree: number;
  pass_through_ratio: number;
  risk_level: string;
  reason: string;
}

export interface PredictionResult {
  complaint_details: any;
  mule_chain: any[];
  flagged_nodes: FlaggedNode[];
  predicted_hotspots: Alert[];
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface DashboardProps {
  user: any;
}

function Dashboard({ user }: DashboardProps) {
  const [heatmapData, setHeatmapData] = useState<any>(null);
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);
  const [searchAck, setSearchAck] = useState('');
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null);
  const [jeopardyGrid, setJeopardyGrid] = useState<any>(null);
  const [isTriangulating, setIsTriangulating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mapState = user?.role === 'officer' && user?.station_lat ? {
    longitude: user.station_lon,
    latitude: user.station_lat,
    zoom: 9
  } : undefined;

  // Poll for active alerts and heatmap
  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('jwt_token');
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        
        const [heatmapRes, alertsRes] = await Promise.all([
          axios.get(`${API_URL}/api/v1/analytics/risk-heatmap`, { headers }),
          axios.get(`${API_URL}/api/v1/alerts/active`, { headers })
        ]);
        setHeatmapData(heatmapRes.data);
        setActiveAlerts(alertsRes.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
      }
    };

    fetchData();
    const intervalId = setInterval(fetchData, 10000); // 10s polling
    return () => clearInterval(intervalId);
  }, [user]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchAck.trim()) return;
    await doSearch(searchAck.trim());
  };

  const handleDirectSearch = async (ack: string) => {
    setSearchAck(ack);
    await doSearch(ack);
  };

  const doSearch = async (ack: string) => {
    setIsLoading(true);
    setError(null);
    setPredictionResult(null);
    setJeopardyGrid(null); // Clear old grid
    
    try {
      const res = await axios.post(`${API_URL}/api/v1/predict/complaint`, {
        ack_no: ack
      });
      setPredictionResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to trace complaint");
      setPredictionResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Expose to window for Sidebar
  useEffect(() => {
    (window as any).directSearch = handleDirectSearch;
    return () => { delete (window as any).directSearch; };
  }, []);

  const handleTriangulate = async () => {
    if (!predictionResult || predictionResult.predicted_hotspots.length === 0) return;
    
    setIsTriangulating(true);
    try {
      const terminalIds = predictionResult.predicted_hotspots.map(h => h.terminal_id);
      const res = await axios.post(`${API_URL}/api/v1/strategic/triangulate`, {
        terminal_ids: terminalIds
      });
      setJeopardyGrid(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to triangulate hideout.");
    } finally {
      setIsTriangulating(false);
    }
  };

  return (
    <div className="flex h-full w-full bg-slate-900 text-slate-100 overflow-hidden font-sans">
      
      <Sidebar 
        activeAlerts={activeAlerts} 
        predictionResult={predictionResult}
        onTriangulate={handleTriangulate}
        isTriangulating={isTriangulating}
        onClearPrediction={() => setPredictionResult(null)}
      />

      <main className="flex-1 relative flex flex-col">
        {/* Top Navbar / Search */}
        <header className="absolute top-0 z-10 w-full p-4 pointer-events-none">
          <div className="max-w-2xl mx-auto flex items-center gap-3 bg-slate-900/70 backdrop-blur-md pointer-events-auto rounded-xl border border-white/10 shadow-2xl p-2 overflow-hidden">
            <form onSubmit={handleSearch} className="flex-1 flex gap-3 relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                <Search size={18} />
              </div>
              <input
                id="search-ack-input"
                type="text"
                value={searchAck}
                onChange={(e) => setSearchAck(e.target.value)}
                placeholder="Enter 14-digit NCRP ACK No (e.g. 31408498669438)..."
                className="w-full bg-slate-950/50 text-slate-100 placeholder-slate-500 pl-10 pr-4 py-2.5 rounded-lg outline-none border border-white/5 focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all font-mono text-sm shadow-inner"
              />
              <button 
                id="predict-btn"
                type="submit" 
                disabled={isLoading}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold tracking-wide py-2.5 px-6 rounded-lg transition-all shadow-lg shadow-blue-900/20 disabled:opacity-50 border border-blue-500/30"
              >
                {isLoading ? 'TRACING...' : 'PREDICT'}
              </button>
            </form>
          </div>
          {error && (
            <div className="max-w-2xl mx-auto mt-3 bg-red-950/80 text-red-200 p-3 rounded-lg pointer-events-auto text-center border border-red-500/30 shadow-lg text-sm font-medium backdrop-blur-sm">
              {error}
            </div>
          )}
        </header>

        {/* Mapbox Area */}
        <div className="flex-1">
          <MapComponent 
            heatmapData={heatmapData} 
            predictionResult={predictionResult}
            jeopardyGrid={jeopardyGrid}
            initialViewState={mapState}
            user={user}
          />
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
