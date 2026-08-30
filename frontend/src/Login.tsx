import React, { useState } from 'react';
import { Shield, Lock } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface LoginProps {
  onLogin: (token: string, user: any) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await axios.post(`${API_URL}/api/v1/auth/token`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      const { access_token, user } = res.data;
      onLogin(access_token, user);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4 font-sans">
      <div className="bg-slate-800 p-8 rounded-lg shadow-2xl max-w-md w-full border border-slate-700">
        <div className="flex flex-col items-center justify-center mb-8">
          <Shield className="text-blue-500 mb-4" size={48} />
          <h1 className="text-2xl font-bold text-white tracking-widest text-center">I4C COMMAND CENTER</h1>
          <p className="text-slate-400 text-sm mt-2">Law Enforcement Portal</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Officer ID / Username</label>
            <input 
              type="text" 
              required
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full bg-slate-900 border border-slate-600 rounded p-3 text-white focus:border-blue-500 outline-none"
              placeholder="e.g. jamtara_officer"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Passcode</label>
            <div className="relative">
              <input 
                type="password" 
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-600 rounded p-3 pl-10 text-white focus:border-blue-500 outline-none"
                placeholder="••••••••"
              />
              <Lock className="absolute left-3 top-3.5 text-slate-500" size={18} />
            </div>
          </div>

          {error && <div className="text-red-400 text-sm text-center">{error}</div>}

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded transition-colors disabled:opacity-50 mt-4"
          >
            {isLoading ? 'AUTHENTICATING...' : 'SECURE LOGIN'}
          </button>
        </form>
        
        <div className="mt-8 pt-6 border-t border-slate-700 text-center">
          <p className="text-xs text-slate-400 mb-3">Are you a citizen reporting a crime?</p>
          <a href="/" className="inline-block w-full bg-slate-700 hover:bg-slate-600 text-white text-sm py-2 px-4 rounded transition-colors">
            Switch to Citizen Portal
          </a>
        </div>
      </div>
      <div className="mt-8 text-center text-[10px] text-slate-500 uppercase tracking-widest">
        Proprietary Intelligence System &bull; Government of India
      </div>
    </div>
  );
};

export default Login;
