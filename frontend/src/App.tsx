import React, { useState } from 'react';
import Login from './Login';
import Dashboard from './Dashboard';
import Statistics from './Statistics';
import { Shield, Map as MapIcon, BarChart3, LogOut } from 'lucide-react';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'statistics'>('dashboard');

  if (!isAuthenticated) {
    return <Login onLogin={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900 overflow-hidden font-sans">
      
      {/* Top Application Navbar */}
      <nav className="bg-slate-800 border-b border-slate-700 p-3 flex justify-between items-center z-50 shadow-md">
        <div className="flex items-center ml-4">
          <Shield className="w-6 h-6 text-blue-500 mr-2" />
          <span className="font-bold text-white tracking-widest uppercase">I4C Command Center</span>
        </div>
        
        <div className="flex items-center space-x-2 mr-4">
          <button 
            onClick={() => setCurrentPage('dashboard')}
            className={`flex items-center px-4 py-2 rounded transition-colors ${
              currentPage === 'dashboard' 
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' 
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700'
            }`}
          >
            <MapIcon className="w-4 h-4 mr-2" />
            <span className="font-semibold text-sm uppercase tracking-wider">Live Map</span>
          </button>
          
          <button 
            onClick={() => setCurrentPage('statistics')}
            className={`flex items-center px-4 py-2 rounded transition-colors ${
              currentPage === 'statistics' 
                ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30' 
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700'
            }`}
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            <span className="font-semibold text-sm uppercase tracking-wider">Analytics</span>
          </button>

          <div className="w-px h-6 bg-slate-600 mx-2"></div>

          <button 
            onClick={() => setIsAuthenticated(false)}
            className="flex items-center px-3 py-2 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded transition-colors"
            title="Secure Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {currentPage === 'dashboard' ? <Dashboard /> : <Statistics />}
      </div>

    </div>
  );
}

export default App;
