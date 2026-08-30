import React, { useState } from 'react';
import { User, Phone, Fingerprint } from 'lucide-react';

interface CitizenLoginProps {
  onLoginSuccess: (aadhar: string, phone: string) => void;
  onSwitchToLea: () => void;
}

const CitizenLogin: React.FC<CitizenLoginProps> = ({ onLoginSuccess, onSwitchToLea }) => {
  const [aadhar, setAadhar] = useState('');
  const [phone, setPhone] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsVerifying(true);
    // Simulate OTP verification delay for demo
    setTimeout(() => {
      setIsVerifying(false);
      onLoginSuccess(aadhar, phone);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4 font-sans">
      <div className="bg-slate-800 p-8 rounded-lg shadow-2xl max-w-md w-full border border-slate-700">
        <div className="flex flex-col items-center justify-center mb-8">
          <div className="bg-green-900/50 p-4 rounded-full mb-4 border border-green-500/30">
            <User className="text-green-400" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-widest text-center">CITIZEN PORTAL</h1>
          <p className="text-slate-400 text-sm mt-2">National Cybercrime Reporting</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Aadhar Number</label>
            <div className="relative">
              <input 
                type="text" 
                required
                pattern="[0-9]{12}"
                maxLength={12}
                value={aadhar}
                onChange={e => setAadhar(e.target.value.replace(/\D/g, ''))}
                className="w-full bg-slate-900 border border-slate-600 rounded p-3 pl-10 text-white focus:border-green-500 outline-none"
                placeholder="12-digit Aadhar"
              />
              <Fingerprint className="absolute left-3 top-3.5 text-slate-500" size={18} />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Phone Number</label>
            <div className="relative">
              <input 
                type="text" 
                required
                pattern="[0-9]{10}"
                maxLength={10}
                value={phone}
                onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
                className="w-full bg-slate-900 border border-slate-600 rounded p-3 pl-10 text-white focus:border-green-500 outline-none"
                placeholder="10-digit Mobile"
              />
              <Phone className="absolute left-3 top-3.5 text-slate-500" size={18} />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={isVerifying}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded transition-colors disabled:opacity-50 mt-4"
          >
            {isVerifying ? 'VERIFYING OTP...' : 'LOGIN VIA AADHAR'}
          </button>
        </form>
        
        <div className="mt-8 pt-6 border-t border-slate-700 text-center">
          <p className="text-xs text-slate-400 mb-3">Are you Law Enforcement Personnel?</p>
          <button 
            onClick={onSwitchToLea}
            className="w-full bg-slate-700 hover:bg-slate-600 text-white text-sm py-2 px-4 rounded transition-colors"
          >
            Switch to Officer / Admin Login
          </button>
        </div>
      </div>
      
      <div className="mt-8 text-center text-[10px] text-slate-500 uppercase tracking-widest">
        Proprietary Intelligence System &bull; Government of India
      </div>
    </div>
  );
};

export default CitizenLogin;
