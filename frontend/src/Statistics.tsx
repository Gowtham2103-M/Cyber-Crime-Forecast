import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart3, TrendingUp, AlertTriangle, IndianRupee, ShieldAlert, Activity } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Statistics: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_URL}/api/v1/analytics/stats`)
      .then(res => {
        setStats(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="flex h-screen items-center justify-center bg-slate-900 text-blue-400">Loading Global Intelligence...</div>;
  }

  if (!stats) {
    return <div className="flex h-screen items-center justify-center bg-slate-900 text-red-400">Failed to load statistics.</div>;
  }

  return (
    <div className="flex-1 bg-slate-900 text-slate-100 p-8 overflow-y-auto">
      <div className="max-w-6xl mx-auto">
        
        <header className="mb-10 flex items-center justify-between border-b border-slate-700 pb-4">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-wide flex items-center">
              <Activity className="w-8 h-8 mr-3 text-blue-500" />
              NATIONWIDE THREAT ANALYTICS
            </h1>
            <p className="text-slate-400 mt-2">Aggregate metrics extracted from the National Cybercrime Reporting Portal (NCRP).</p>
          </div>
        </header>

        {/* Top KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-slate-400 font-semibold text-sm uppercase">Total Active Cases</h3>
              <ShieldAlert className="w-5 h-5 text-red-500" />
            </div>
            <p className="text-4xl font-bold text-white">{stats.total_complaints.toLocaleString()}</p>
          </div>

          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-slate-400 font-semibold text-sm uppercase">Total Defrauded Funds</h3>
              <IndianRupee className="w-5 h-5 text-green-500" />
            </div>
            <p className="text-3xl font-bold text-green-400">
              ₹{(stats.total_defrauded_amount / 10000000).toFixed(2)} Cr
            </p>
          </div>

          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-slate-400 font-semibold text-sm uppercase">Primary Crime Modus</h3>
              <AlertTriangle className="w-5 h-5 text-orange-500" />
            </div>
            <p className="text-xl font-bold text-white truncate">
              {Object.keys(stats.top_crimes)[0].replace('_', ' ')}
            </p>
          </div>

          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-slate-400 font-semibold text-sm uppercase">Top Extraction Method</h3>
              <TrendingUp className="w-5 h-5 text-blue-500" />
            </div>
            <p className="text-xl font-bold text-white truncate">
              {Object.keys(stats.top_cashout_terminals)[0]} Withdrawals
            </p>
          </div>
        </div>

        {/* Charts / Lists section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Victim States */}
          <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
            <div className="bg-slate-800/50 p-4 border-b border-slate-700 flex items-center">
              <BarChart3 className="w-5 h-5 text-purple-400 mr-2" />
              <h2 className="text-lg font-semibold uppercase tracking-wider text-slate-200">Most Affected Victim States</h2>
            </div>
            <div className="p-6">
              <div className="space-y-5">
                {Object.entries(stats.top_victim_states).map(([state, count]: any, idx) => (
                  <div key={state}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-slate-200">{state}</span>
                      <span className="text-purple-400">{count} Victims</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full" 
                        style={{ width: `${(count / Object.values(stats.top_victim_states)[0] as number) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Crime Categories */}
          <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
            <div className="bg-slate-800/50 p-4 border-b border-slate-700 flex items-center">
              <AlertTriangle className="w-5 h-5 text-orange-400 mr-2" />
              <h2 className="text-lg font-semibold uppercase tracking-wider text-slate-200">Crime Category Distribution</h2>
            </div>
            <div className="p-6">
              <div className="space-y-5">
                {Object.entries(stats.top_crimes).map(([crime, count]: any, idx) => (
                  <div key={crime}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-slate-200">{crime.replace('_', ' ')}</span>
                      <span className="text-orange-400">{count} Cases</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-orange-600 to-yellow-500 h-2 rounded-full" 
                        style={{ width: `${(count / Object.values(stats.top_crimes)[0] as number) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Statistics;
