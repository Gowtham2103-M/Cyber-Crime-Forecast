import React, { useState, useEffect } from 'react';
import axios from 'axios';
import MapComponent from './MapComponent';
import Sidebar from './Sidebar';
import { Search } from 'lucide-react';

export interface Alert {
  terminal_id: string;
  latitude: number;
  longitude: number;
  terminal_type: string;
  risk_score: number;
  time_window_start: string;
  time_window_end: string;
  expected_cashout_amount: number;
  explanation?: {
    baseline_spatial_pct: number;
    recent_activity_pct: number;
    network_link_pct: number;
    details: string[];
  };
}

export interface PredictionResult {
  complaint_details: any;
  mule_chain: any[];
  predicted_hotspots: Alert[];
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [heatmapData, setHeatmapData] = useState<any>(null);
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);
  const [searchAck, setSearchAck] = useState('');
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Poll for active alerts and heatmap
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [heatmapRes, alertsRes] = await Promise.all([
          axios.get(`${API_URL}/api/v1/analytics/risk-heatmap`),
          axios.get(`${API_URL}/api/v1/alerts/active`)
        ]);
        setHeatmapData(heatmapRes.data);
        setActiveAlerts(alertsRes.data);
      } catch (err) {
        console.error("Error fetching polling data:", err);
      }
    };

    fetchData();
    const intervalId = setInterval(fetchData, 10000); // 10s polling
    return () => clearInterval(intervalId);
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchAck.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setPredictionResult(null);
    
    try {
      const res = await axios.post(`${API_URL}/api/v1/predict/complaint`, {
        ack_no: searchAck.trim()
      });
      setPredictionResult(res.data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to fetch prediction");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full bg-slate-900 text-slate-100 overflow-hidden font-sans">
      
      <Sidebar activeAlerts={activeAlerts} predictionResult={predictionResult} />

      <main className="flex-1 relative flex flex-col">
        {/* Top Navbar / Search */}
        <header className="absolute top-0 z-10 w-full p-4 pointer-events-none">
          <div className="max-w-2xl mx-auto flex items-center bg-slate-800/80 backdrop-blur pointer-events-auto rounded-lg border border-slate-700 shadow-xl overflow-hidden">
            <div className="p-3 text-slate-400">
              <Search size={20} />
            </div>
            <form onSubmit={handleSearch} className="flex-1 flex">
              <input 
                type="text" 
                placeholder="Enter 14-digit NCRP ACK No (e.g. 31408498669438)..." 
                className="w-full bg-transparent p-3 outline-none text-slate-100 placeholder-slate-500"
                value={searchAck}
                onChange={(e) => setSearchAck(e.target.value)}
              />
              <button 
                type="submit" 
                disabled={isLoading}
                className="bg-blue-600 hover:bg-blue-700 px-6 py-3 font-semibold transition-colors disabled:opacity-50"
              >
                {isLoading ? 'TRACING...' : 'PREDICT'}
              </button>
            </form>
          </div>
          {error && (
            <div className="max-w-2xl mx-auto mt-2 bg-red-900/80 text-red-200 p-3 rounded pointer-events-auto text-center border border-red-700">
              {error}
            </div>
          )}
        </header>

        {/* Mapbox Area */}
        <div className="flex-1">
          <MapComponent 
            heatmapData={heatmapData} 
            predictionResult={predictionResult} 
          />
        </div>
      </main>
    </div>
  );
}

export default App;
