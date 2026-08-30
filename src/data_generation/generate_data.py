import os
import uuid
import random
import numpy as np
import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
from faker import Faker
import argparse

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

fake = Faker('en_IN')

# Define hotspots (Latitude, Longitude) with weights to create Major vs Minor hubs
HOTSPOTS = [
    # Flattened weights so Jamtara doesn't overpower Nuh and others
    {"coords": (23.9583, 86.8142), "weight": 0.15}, # Jamtara, Jharkhand
    {"coords": (28.1130, 77.0102), "weight": 0.15}, # Nuh/Mewat, Haryana
    {"coords": (28.5355, 77.3910), "weight": 0.15}, # Noida, Delhi NCR
    {"coords": (24.1950, 86.3021), "weight": 0.15}, # Deoghar, Jharkhand
    
    # MINOR HUBS (Spread out across India)
    {"coords": (30.9009, 75.8572), "weight": 0.10}, # Ludhiana, Punjab
    {"coords": (19.0760, 72.8777), "weight": 0.10}, # Mumbai, Maharashtra
    {"coords": (13.0826, 80.2707), "weight": 0.10}, # Chennai, Tamil Nadu
    {"coords": (22.5726, 88.3638), "weight": 0.10}  # Kolkata, West Bengal
]

class SyntheticDataGenerator:
    """
    Generates synthetic data for cybercrime financial networks.
    - Uses Barabasi-Albert model for mule networks (hub and spoke topology).
    - Log-Normal distribution for reporting delays.
    - Exponential distribution for transaction delays.
    - GMM-based approach for ATM withdrawal locations.
    """
    def __init__(self, num_complaints=5000, num_mules=2000):
        self.num_complaints = num_complaints
        self.num_mules = num_mules
        self.mule_network = self._create_mule_network()
        
        # Select entry nodes for complaints
        # In a real scenario, victims send money to a subset of mules (the spokes/entry points)
        self.entry_mules = list(self.mule_network.nodes)[:self.num_complaints] 
        
        # Pre-generate random, hashed-looking account numbers for all mules
        self.mule_accounts = {i: fake.sha256()[:16] for i in range(self.num_mules)}
        
        # Assign a specific hotspot to each mule based on weights
        self.mule_hotspots = {}
        weights = [h["weight"] for h in HOTSPOTS]
        for i in range(self.num_mules):
            self.mule_hotspots[i] = random.choices(HOTSPOTS, weights=weights, k=1)[0]["coords"]
        
        self.states = [
            "Maharashtra", "Karnataka", "Delhi", "Uttar Pradesh", "Telangana",
            "Tamil Nadu", "Gujarat", "West Bengal", "Rajasthan", "Kerala"
        ]
        self.crime_categories = ["UPI_Fraud", "Investment_Scam", "KYC_Fraud", "Sextortion"]
        self.terminal_types = ["ATM", "MICRO_ATM_CSP", "POS"]

    def _create_mule_network(self):
        """
        Creates a scale-free mule network using the Barabási-Albert model.
        Hub-and-spoke model mimicking cybercrime layering networks where a few accounts
        act as major aggregators.
        """
        return nx.barabasi_albert_graph(self.num_mules, m=2)

    def generate_complaints(self):
        """
        Generates NCRP complaints with log-normal reporting delays.
        """
        complaints = []
        base_time = datetime(2023, 1, 1)
        
        for i in range(self.num_complaints):
            # ack_no: 14-digit numeric string
            ack_no = f"3140{fake.random_number(digits=10, fix_len=True)}"
            
            # Incident time
            days_offset = np.random.randint(0, 365)
            hours_offset = np.random.randint(0, 24)
            mins_offset = np.random.randint(0, 60)
            incident_time = base_time + timedelta(days=days_offset, hours=hours_offset, minutes=mins_offset)
            
            # Temporal Delay (Log-Normal): Most report in 1-4 hours, some take days
            # We use a log-normal distribution to generate delay in hours
            delay_hours = np.random.lognormal(mean=1.5, sigma=1.0)
            reported_time = incident_time + timedelta(hours=delay_hours)
            
            crime_cat = np.random.choice(self.crime_categories, p=[0.4, 0.3, 0.2, 0.1])
            
            # Defrauded amount between 10k and 500k
            defrauded_amount = round(np.random.uniform(10000, 500000), 2)
            
            # Link to an entry mule account in the network
            # Wrap around if num_complaints > num_mules
            initial_mule_id = self.entry_mules[i % len(self.entry_mules)]
            initial_upi = f"{self.mule_accounts[initial_mule_id]}@upi"
            
            victim_state = np.random.choice(self.states)
            
            complaints.append({
                'ack_no': ack_no,
                'incident_timestamp': incident_time,
                'reported_timestamp': reported_time,
                'crime_category': crime_cat,
                'defrauded_amount': defrauded_amount,
                'initial_beneficiary_upi': initial_upi,
                'victim_state': victim_state,
                '_entry_mule_id': initial_mule_id # Used internally for linking
            })
        
        self.complaints_df = pd.DataFrame(complaints)
        return self.complaints_df

    def _get_hotspot_location(self, mule_id):
        """
        Spatial Point Processes (GMM): 
        Samples coordinates using a Gaussian distribution around the mule's assigned regional hotspot.
        """
        hotspot = self.mule_hotspots[mule_id]
        lat_offset = np.random.normal(0, 0.05) # approx 5km variance
        lon_offset = np.random.normal(0, 0.05)
        return round(hotspot[0] + lat_offset, 6), round(hotspot[1] + lon_offset, 6)

    def generate_transactions_and_cashouts(self):
        """
        Simulates the flow of money through the mule network (CFCFRMS) and eventual cashouts (ATM).
        """
        transactions = []
        cashouts = []
        
        for _, complaint in self.complaints_df.iterrows():
            current_mule = complaint['_entry_mule_id']
            amount = complaint['defrauded_amount']
            current_time = complaint['incident_timestamp']
            
            # Start at layer 1
            layer = 1
            max_layers = np.random.randint(2, 6) # Between 2 and 5 layers of hops before cashout
            
            # Active funds queue: (current_mule_id, amount, current_timestamp, current_layer)
            active_funds = [(current_mule, amount, current_time, layer)]
            
            while active_funds:
                curr_mule, curr_amount, curr_time, curr_layer = active_funds.pop(0)
                
                # Condition to Cashout: Max layers reached, or amount is too small to split further
                if curr_layer >= max_layers or curr_amount < 5000:
                    cashout_id = str(uuid.uuid4())
                    term_type = np.random.choice(self.terminal_types, p=[0.6, 0.3, 0.1])
                    # Generate a realistic terminal ID
                    term_id = f"{term_type[:3]}-{fake.lexify('????').upper()}-{fake.numerify('####')}"
                    
                    # Delay before cashout (Exponential distribution, avg 30 mins)
                    cashout_delay_mins = np.random.exponential(scale=30)
                    cashout_time = curr_time + timedelta(minutes=cashout_delay_mins)
                    lat, lon = self._get_hotspot_location(curr_mule)
                    
                    cashouts.append({
                        'cashout_id': cashout_id,
                        'mule_account': self.mule_accounts[curr_mule],
                        'terminal_id': term_id,
                        'terminal_type': term_type,
                        'amount_withdrawn': curr_amount,
                        'timestamp': cashout_time,
                        'latitude': lat,
                        'longitude': lon
                    })
                    continue
                
                # Layering: Transfer to next layer (fan out)
                neighbors = list(self.mule_network.neighbors(curr_mule))
                if not neighbors:
                    # Dead end in the graph, force cashout
                    active_funds.append((curr_mule, curr_amount, curr_time, max_layers))
                    continue
                
                # Fan out to 1 to 3 next mules
                num_splits = min(len(neighbors), np.random.randint(1, 4))
                next_mules = random.sample(neighbors, num_splits)
                
                # Mass Conservation: retain 5% mule commission, pass on 95%
                transferable_amount = curr_amount * 0.95
                split_amount = round(transferable_amount / num_splits, 2)
                
                for next_mule in next_mules:
                    txn_utr = f"{fake.random_number(digits=12, fix_len=True)}"
                    
                    # Temporal Delay (Exponential): Delay between automated hops, avg 5 mins
                    hop_delay_mins = np.random.exponential(scale=5) 
                    hop_time = curr_time + timedelta(minutes=hop_delay_mins)
                    
                    channel = np.random.choice(["UPI", "IMPS", "NEFT"], p=[0.7, 0.2, 0.1])
                    
                    transactions.append({
                        'txn_utr': txn_utr,
                        'source_account': self.mule_accounts[curr_mule],
                        'beneficiary_account': self.mule_accounts[next_mule],
                        'amount': split_amount,
                        'timestamp': hop_time,
                        'layer_depth': curr_layer,
                        'channel': channel
                    })
                    
                    active_funds.append((next_mule, split_amount, hop_time, curr_layer + 1))
        
        # Inject Benign (Class 0) Normal Traffic so GNN has negative samples
        print("Injecting Benign Background Traffic...")
        benign_accounts = [fake.sha256()[:16] for _ in range(3000)]
        base_time = datetime(2023, 1, 1)
        for _ in range(15000):
            src = random.choice(benign_accounts)
            dst = random.choice(benign_accounts)
            if src != dst:
                transactions.append({
                    'txn_utr': str(fake.random_number(digits=12, fix_len=True)),
                    'source_account': src,
                    'beneficiary_account': dst,
                    'amount': round(np.random.uniform(500, 25000), 2),
                    'timestamp': base_time + timedelta(days=np.random.randint(0, 365), hours=np.random.randint(0, 24)),
                    'layer_depth': 0, # Normal transactions don't have deep mule layering
                    'channel': np.random.choice(["UPI", "IMPS", "NEFT"])
                })
                
        self.transactions_df = pd.DataFrame(transactions)
        self.cashouts_df = pd.DataFrame(cashouts)
        
        # Cleanup internal mapping used for logic
        self.complaints_df.drop(columns=['_entry_mule_id'], inplace=True)
        
        return self.transactions_df, self.cashouts_df

    def save_data(self, output_dir="data"):
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to CSV
        complaints_path = os.path.join(output_dir, 'ncrp_complaints.csv')
        transactions_path = os.path.join(output_dir, 'cfcfrms_transactions.csv')
        cashouts_path = os.path.join(output_dir, 'atm_cashouts.csv')
        
        self.complaints_df.to_csv(complaints_path, index=False)
        self.transactions_df.to_csv(transactions_path, index=False)
        self.cashouts_df.to_csv(cashouts_path, index=False)
        
        print(f"Data successfully saved to:")
        print(f" - {complaints_path} ({len(self.complaints_df)} records)")
        print(f" - {transactions_path} ({len(self.transactions_df)} records)")
        print(f" - {cashouts_path} ({len(self.cashouts_df)} records)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic data for cybercrime analytics.")
    parser.add_argument('--complaints', type=int, default=1000, help='Number of initial complaints to generate')
    parser.add_argument('--mules', type=int, default=500, help='Number of mule accounts in the network')
    parser.add_argument('--output', type=str, default='data', help='Output directory for CSV files')
    args = parser.parse_args()

    print(f"Initializing Data Generator with {args.complaints} complaints and {args.mules} mules...")
    generator = SyntheticDataGenerator(num_complaints=args.complaints, num_mules=args.mules)
    
    print("Generating NCRP Complaints...")
    generator.generate_complaints()
    
    print("Generating Mule Network Transactions and ATM Cashouts...")
    generator.generate_transactions_and_cashouts()
    
    print("Saving to CSV...")
    generator.save_data(output_dir=args.output)
    print("Pipeline execution complete.")
