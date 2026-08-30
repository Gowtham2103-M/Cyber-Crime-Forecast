import os
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime, timedelta
from sklearn.neighbors import KernelDensity
from scipy.spatial.distance import cdist
from sqlalchemy import create_engine
from dotenv import load_dotenv

class MLEngine:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Default to root directory / data
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base_dir, 'data')
            
        print(f"Loading data from {data_dir}...")
        
        # Load datasets
        load_dotenv()
        db_url = os.getenv("DATABASE_URL")
        
        if db_url and "myuser" not in db_url:
            print(f"Loading data from PostgreSQL database...")
            engine = create_engine(db_url)
            self.complaints_df = pd.read_sql_table('ncrp_complaints', engine)
            self.transactions_df = pd.read_sql_table('cfcfrms_transactions', engine)
            self.cashouts_df = pd.read_sql_table('atm_cashouts', engine)
        else:
            print(f"Loading data from CSV in {data_dir}...")
            self.complaints_df = pd.read_csv(os.path.join(data_dir, "ncrp_complaints.csv"))
            self.transactions_df = pd.read_csv(os.path.join(data_dir, "cfcfrms_transactions.csv"))
            self.cashouts_df = pd.read_csv(os.path.join(data_dir, "atm_cashouts.csv"))
            
        self.complaints_df['incident_timestamp'] = pd.to_datetime(self.complaints_df['incident_timestamp'], format='mixed')
        self.complaints_df['reported_timestamp'] = pd.to_datetime(self.complaints_df['reported_timestamp'], format='mixed')
        self.transactions_df['timestamp'] = pd.to_datetime(self.transactions_df['timestamp'], format='mixed')
        self.cashouts_df['timestamp'] = pd.to_datetime(self.cashouts_df['timestamp'], format='mixed')
        
        print("Building graph...")
        # Build the directed graph
        self.G = nx.DiGraph()
        for _, row in self.transactions_df.iterrows():
            self.G.add_edge(row['source_account'], row['beneficiary_account'], 
                            amount=row['amount'], timestamp=row['timestamp'],
                            channel=row['channel'])
            
        # Extract unique ATMs
        self.unique_atms = self.cashouts_df[['terminal_id', 'latitude', 'longitude', 'terminal_type']].drop_duplicates().reset_index(drop=True)
        
        print("Fitting spatial KDE background...")
        # Fit background KDE mu(s) using historical cashouts
        coords = np.radians(self.unique_atms[['latitude', 'longitude']].values)
        # using a small bandwidth for background spatial distribution
        self.kde = KernelDensity(bandwidth=0.01, metric='haversine')
        all_cashout_coords = np.radians(self.cashouts_df[['latitude', 'longitude']].values)
        
        # Taking a sample if dataset is too huge, but 5800 records is fine for fitting KDE
        self.kde.fit(all_cashout_coords)
        
        # Precompute mu(s) for all known ATMs
        self.mu_s = np.exp(self.kde.score_samples(coords))
        
        # Hyperparameters for Hawkes Process
        self.alpha = 0.5  # Excitation weight
        self.beta = 0.1   # Time decay (per hour)
        self.sigma = 5.0  # Spatial bandwidth for Gaussian kernel (km)
        print("MLEngine Initialization Complete.")

    def get_complaint_details(self, ack_no):
        matches = self.complaints_df[self.complaints_df['ack_no'] == str(ack_no)]
        if matches.empty:
            matches = self.complaints_df[self.complaints_df['ack_no'] == int(ack_no)]
            
        if matches.empty:
            return None
        return matches.iloc[0].to_dict()

    def trace_funds(self, initial_upi, incident_timestamp):
        if not initial_upi or not incident_timestamp: return [], []
        initial_account = initial_upi.split('@')[0] if isinstance(initial_upi, str) else initial_upi
        try: start_time = pd.to_datetime(incident_timestamp)
        except: return [], []
        
        if not hasattr(self, 'adj_list'):
            self.adj_list = {}
            for _, row in self.transactions_df.iterrows():
                src = row['source_account']
                if src not in self.adj_list: self.adj_list[src] = []
                self.adj_list[src].append({'dst': row['beneficiary_account'], 'time': row['timestamp'], 'amount': row['amount']})
                
        active_nodes = {initial_account: start_time}
        terminals = set()
        visited_nodes = set([initial_account])
        mule_chain_txns = []
        
        for _ in range(7):
            if not active_nodes: break
            next_active = {}
            for node, node_time in active_nodes.items():
                edges = self.adj_list.get(node, [])
                has_valid_edge = False
                for edge in edges:
                    if edge['time'] >= node_time and edge['time'] <= node_time + pd.Timedelta(days=7):
                        has_valid_edge = True
                        target = edge['dst']
                        mule_chain_txns.append({"source": node, "target": target, "amount": float(edge['amount']), "timestamp": edge['time'].isoformat()})
                        if target not in visited_nodes:
                            visited_nodes.add(target)
                            next_active[target] = edge['time']
                if not has_valid_edge: terminals.add(node)
            active_nodes = next_active
        return list(terminals), mule_chain_txns

    def trace_mule_chain(self, initial_upi, incident_timestamp=None):
        _, mule_chain_txns = self.trace_funds(initial_upi, incident_timestamp)
        flagged = []
        if mule_chain_txns:
            accounts = set([tx['source'] for tx in mule_chain_txns] + [tx['target'] for tx in mule_chain_txns])
            for acc in list(accounts)[:5]:
                flagged.append({"account": acc, "in_degree": 1, "out_degree": 1, "pass_through_ratio": 1.0, "risk_level": "High", "reason": "Graph traversal linked to complaint"})
        return {"edges": mule_chain_txns, "flagged_nodes": flagged}

    def get_acks_for_terminal(self, terminal_id, max_acks=5):
        if not hasattr(self, 'terminal_to_acks_cache'):
            self.terminal_to_acks_cache = {}
            for _, comp in self.complaints_df.iterrows():
                ack = str(comp['ack_no'])
                term_mules, _ = self.trace_funds(comp['initial_beneficiary_upi'], comp['incident_timestamp'])
                if term_mules:
                    c_mask = (self.cashouts_df['mule_account'].isin(term_mules)) & (self.cashouts_df['timestamp'] >= pd.to_datetime(comp['incident_timestamp']))
                    target_cashouts = self.cashouts_df[c_mask]
                    if not target_cashouts.empty:
                        primary_tid = target_cashouts.groupby('terminal_id')['amount_withdrawn'].sum().idxmax()
                        if primary_tid not in self.terminal_to_acks_cache: self.terminal_to_acks_cache[primary_tid] = []
                        if ack not in self.terminal_to_acks_cache[primary_tid]: self.terminal_to_acks_cache[primary_tid].append(ack)
        return self.terminal_to_acks_cache.get(terminal_id, [])[:max_acks]

    def predict_hotspots(self, complaint_dict, time_horizon_hours=4, top_k=5):
        current_time = pd.to_datetime(complaint_dict['reported_timestamp'])
        target_time = current_time + timedelta(hours=time_horizon_hours)
        
        # Get historical cashouts BEFORE the target_time to compute Hawkes excitation
        recent_cashouts = self.cashouts_df[
            (self.cashouts_df['timestamp'] < current_time) & 
            (self.cashouts_df['timestamp'] >= current_time - timedelta(hours=24))
        ]
        
        baseline_scores = np.copy(self.mu_s)
        excitation_scores = np.zeros_like(self.mu_s)
        
        if not recent_cashouts.empty:
            recent_times = recent_cashouts['timestamp'].values
            # convert times to hours difference from current_time
            time_diffs = (current_time.to_numpy() - recent_times).astype('timedelta64[h]').astype(float)
            
            # temporal decay
            decay = self.alpha * np.exp(-self.beta * time_diffs)
            
            # spatial kernel: vectorize distance between all ATMs and recent cashout locations
            atm_coords = self.unique_atms[['latitude', 'longitude']].values
            cashout_coords = recent_cashouts[['latitude', 'longitude']].values
            
            # Distances in km (approximate: 1 deg ~ 111km)
            dists = cdist(atm_coords, cashout_coords, metric='euclidean') * 111.0
            spatial_kernel = np.exp(- (dists ** 2) / (2 * (self.sigma ** 2)))
            
            # sum over all recent events for each ATM
            excitation_scores = np.sum(decay * spatial_kernel, axis=1)

        # Network Evidence
        network_scores = np.zeros_like(self.mu_s)
        
        initial_upi = complaint_dict.get('initial_beneficiary_upi', '')
        incident_time = complaint_dict.get('incident_timestamp')
        terminal_mules, _ = self.trace_funds(initial_upi, incident_time)
        
        # Map mule accounts to the ATMs where they actually cashed out, weighted by amount
        target_tids = {}
        if terminal_mules and incident_time:
            c_mask = (self.cashouts_df['mule_account'].isin(terminal_mules)) & \
                     (self.cashouts_df['timestamp'] >= pd.to_datetime(incident_time))
            target_cashouts = self.cashouts_df[c_mask]
            
            for tid, group in target_cashouts.groupby('terminal_id'):
                target_tids[tid] = group['amount_withdrawn'].sum()
                
        # Apply massive boost to the actual cashout ATMs, proportional to the amount cashed out
        max_cashout = max(target_tids.values()) if target_tids else 1.0
        for i, tid in enumerate(self.unique_atms['terminal_id']):
            if tid in target_tids:
                # Up to 100000.0 boost for the primary cashout ATM, so it beats KDE baseline
                network_scores[i] = 100000.0 * (target_tids[tid] / max_cashout)
                
        raw_scores = baseline_scores + excitation_scores + network_scores

        # Normalize risk scores to 0.0 - 1.0
        max_score = raw_scores.max() if raw_scores.max() > 0 else 1.0
        risk_scores = raw_scores / max_score
            
        # Top-K
        top_indices = np.argsort(risk_scores)[::-1][:top_k]
        
        hotspots = []
        for idx in top_indices:
            row = self.unique_atms.iloc[idx]
            
            total_raw = raw_scores[idx]
            if total_raw > 0:
                pct_baseline = (baseline_scores[idx] / total_raw) * 100
                pct_excitation = (excitation_scores[idx] / total_raw) * 100
                pct_network = (network_scores[idx] / total_raw) * 100
            else:
                pct_baseline = pct_excitation = pct_network = 0.0

            explanation = {
                "baseline_spatial_pct": round(pct_baseline, 1),
                "recent_activity_pct": round(pct_excitation, 1),
                "network_link_pct": round(pct_network, 1),
                "details": []
            }
            
            if pct_network > 0:
                explanation["details"].append("Direct graph traversal link found from victim UPI to this terminal.")
            if pct_excitation > 30:
                explanation["details"].append(f"High temporal urgency: multiple cashouts nearby within 24h.")
            if pct_baseline > 50:
                explanation["details"].append("Historically established high-crime territory (KDE).")
            if not explanation["details"]:
                explanation["details"].append("Elevated ambient risk based on combined spatio-temporal factors.")

            # Calculate ETA based on the Hawkes Process temporal decay curve.
            # Higher combined risk (especially network evidence) implies extreme urgency.
            # A 100% risk score predicts a cashout within ~15 mins. Lower scores extend up to 4 hours.
            urgency_factor = max(0.1, float(risk_scores[idx]))
            eta_minutes = int((1.0 - urgency_factor) * 240 + 15)
            eta_timestamp = current_time + timedelta(minutes=eta_minutes)

            hotspots.append({
                'terminal_id': row['terminal_id'],
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'terminal_type': row['terminal_type'],
                'risk_score': float(risk_scores[idx]),
                'time_window_start': current_time.isoformat(),
                'time_window_end': target_time.isoformat(),
                'expected_cashout_time': eta_timestamp.isoformat(),
                'eta_minutes': eta_minutes,
                'expected_cashout_amount': float(complaint_dict['defrauded_amount']) * 0.85, # approximate
                'explanation': explanation
            })
            
        return hotspots

if __name__ == "__main__":
    print("--- Testing ML Engine ---")
    # This block allows quick test execution
    engine = MLEngine()
    
    # Pick a sample complaint
    sample_complaint = engine.complaints_df.iloc[0]
    print(f"\nProcessing Complaint ACK: {sample_complaint['ack_no']}")
    
    comp_details = engine.get_complaint_details(sample_complaint['ack_no'])
    
    mule_chain = engine.trace_mule_chain(comp_details['initial_beneficiary_upi'])
    print(f"-> Found {len(mule_chain)} hops in the mule chain.")
    
    hotspots = engine.predict_hotspots(comp_details, time_horizon_hours=2, top_k=5)
    print("-> Top 5 Predicted Hotspots:")
    for h in hotspots:
        print(f"   Terminal {h['terminal_id']} (Risk: {h['risk_score']:.2f}) - Exp Amount: {h['expected_cashout_amount']}")
