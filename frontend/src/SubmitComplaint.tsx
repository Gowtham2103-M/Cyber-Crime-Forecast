import React, { useState } from 'react';
import { Shield, AlertTriangle, CheckCircle2 } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SubmitComplaintProps {
  citizenInfo: { aadhar: string, phone: string } | null;
}

function SubmitComplaint({ citizenInfo }: SubmitComplaintProps) {
  const [formData, setFormData] = useState({
    crime_category: 'UPI Fraud',
    defrauded_amount: '',
    initial_beneficiary_upi: '',
    victim_state: 'Maharashtra'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [successAck, setSuccessAck] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccessAck(null);

    try {
      const res = await axios.post(`${API_URL}/api/v1/complaints`, {
        crime_category: formData.crime_category,
        defrauded_amount: parseFloat(formData.defrauded_amount),
        initial_beneficiary_upi: formData.initial_beneficiary_upi,
        victim_state: formData.victim_state,
        aadhar_number: citizenInfo?.aadhar || 'UNKNOWN',
        phone_number: citizenInfo?.phone || 'UNKNOWN'
      });
      setSuccessAck(res.data.ack_no);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit complaint.');
    } finally {
      setIsLoading(false);
    }
  };

  if (successAck) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800 p-8 rounded-lg shadow-2xl max-w-md w-full text-center border border-green-500/30">
          <CheckCircle2 size={64} className="mx-auto text-green-500 mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Complaint Registered</h2>
          <p className="text-slate-300 mb-6">Your complaint has been successfully recorded in the national database.</p>
          <div className="bg-slate-900 p-4 rounded mb-6 font-mono text-xl text-green-400 border border-slate-700">
            ACK: {successAck}
          </div>
          <p className="text-sm text-slate-400 mb-6">Please save this ACK number to track your case.</p>
          <button 
            onClick={() => setSuccessAck(null)}
            className="text-blue-400 hover:text-blue-300 transition-colors"
          >
            Submit Another Complaint
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4 font-sans">
      <div className="bg-slate-800 p-8 rounded-lg shadow-2xl max-w-md w-full border border-slate-700">
        <div className="flex items-center justify-center mb-8">
          <Shield className="text-blue-500 mr-3" size={32} />
          <h1 className="text-2xl font-bold text-white tracking-wider">NCRP PORTAL</h1>
        </div>
        
        <div className="bg-blue-900/20 border border-blue-500/30 p-3 rounded mb-6 flex items-start">
          <AlertTriangle className="text-blue-400 mr-2 shrink-0 mt-0.5" size={16} />
          <p className="text-xs text-blue-200">
            If you have lost money to cyber fraud, please fill out this form immediately. The faster you report, the higher the chance of recovery.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Crime Category</label>
            <select 
              value={formData.crime_category}
              onChange={e => setFormData({...formData, crime_category: e.target.value})}
              className="w-full bg-slate-900 border border-slate-600 rounded p-2.5 text-white focus:border-blue-500 outline-none"
            >
              <option>UPI Fraud</option>
              <option>Credit Card Fraud</option>
              <option>Investment Scam</option>
              <option>Phishing</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Amount Lost (₹)</label>
            <input 
              type="number" 
              required
              min="1"
              value={formData.defrauded_amount}
              onChange={e => setFormData({...formData, defrauded_amount: e.target.value})}
              className="w-full bg-slate-900 border border-slate-600 rounded p-2.5 text-white focus:border-blue-500 outline-none"
              placeholder="e.g. 50000"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Scammer's UPI ID / Account</label>
            <input 
              type="text" 
              required
              value={formData.initial_beneficiary_upi}
              onChange={e => setFormData({...formData, initial_beneficiary_upi: e.target.value})}
              className="w-full bg-slate-900 border border-slate-600 rounded p-2.5 text-white focus:border-blue-500 outline-none"
              placeholder="e.g. scammer@ybl"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Your State</label>
            <select 
              value={formData.victim_state}
              onChange={e => setFormData({...formData, victim_state: e.target.value})}
              className="w-full bg-slate-900 border border-slate-600 rounded p-2.5 text-white focus:border-blue-500 outline-none"
            >
              <option>Maharashtra</option>
              <option>Delhi</option>
              <option>Karnataka</option>
              <option>Haryana</option>
              <option>Jharkhand</option>
            </select>
          </div>

          {error && <div className="text-red-400 text-sm">{error}</div>}

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded transition-colors disabled:opacity-50 mt-4"
          >
            {isLoading ? 'SUBMITTING...' : 'REGISTER COMPLAINT'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default SubmitComplaint;
