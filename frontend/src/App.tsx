import React, { useState, useEffect } from 'react';
import Login from './Login';
import CitizenLogin from './CitizenLogin';
import Dashboard from './Dashboard';
import Statistics from './Statistics';
import SubmitComplaint from './SubmitComplaint';
import { Shield, Map as MapIcon, BarChart3, LogOut } from 'lucide-react';
import axios from 'axios';

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('jwt_token'));
  const [user, setUser] = useState<any>(JSON.parse(localStorage.getItem('user_data') || 'null'));
  const [citizenInfo, setCitizenInfo] = useState<{aadhar: string, phone: string} | null>(null);
  
  // Default to citizen_login if not authenticated
  const [currentPage, setCurrentPage] = useState<'citizen_login' | 'login' | 'dashboard' | 'statistics' | 'complaint'>(token ? 'dashboard' : 'citizen_login');

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      if (currentPage === 'login' || currentPage === 'citizen_login' || currentPage === 'complaint') {
        setCurrentPage('dashboard');
      }
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const handleLogin = (jwt: string, userData: any) => {
    localStorage.setItem('jwt_token', jwt);
    localStorage.setItem('user_data', JSON.stringify(userData));
    setToken(jwt);
    setUser(userData);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('user_data');
    setToken(null);
    setUser(null);
    setCurrentPage('citizen_login');
  };

  // If not authenticated via JWT, handle public routes
  if (!token) {
    if (currentPage === 'login') {
      return <Login onLogin={handleLogin} />;
    } else if (currentPage === 'citizen_login') {
      return <CitizenLogin 
        onLoginSuccess={(aadhar, phone) => {
          setCitizenInfo({ aadhar, phone });
          setCurrentPage('complaint');
        }} 
        onSwitchToLea={() => setCurrentPage('login')} 
      />;
    } else if (currentPage === 'complaint') {
      return (
        <div className="relative">
          <SubmitComplaint citizenInfo={citizenInfo} />
          <button 
            onClick={() => {
              setCitizenInfo(null);
              setCurrentPage('citizen_login');
            }}
            className="absolute top-4 right-4 text-slate-400 hover:text-white text-sm bg-slate-800 px-4 py-2 rounded border border-slate-700 flex items-center shadow-lg"
          >
            <LogOut size={16} className="mr-2" /> Citizen Logout
          </button>
        </div>
      );
    }
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900 overflow-hidden font-sans">
      
      {/* Top Application Navbar */}
      <nav className="bg-slate-800 border-b border-slate-700 p-3 flex justify-between items-center z-50 shadow-md">
        <div className="flex items-center ml-4">
          <Shield className="w-6 h-6 text-blue-500 mr-2" />
          <span className="font-bold text-white tracking-widest uppercase">
            I4C Command Center <span className="text-blue-400 font-mono text-xs ml-2 bg-blue-900/30 px-2 py-0.5 rounded border border-blue-500/30">{user?.role?.toUpperCase()}</span>
          </span>
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
            onClick={handleLogout}
            className="flex items-center px-3 py-2 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded transition-colors"
            title="Secure Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {currentPage === 'dashboard' ? <Dashboard user={user} /> : <Statistics />}
      </div>

    </div>
  );
}

export default App;
