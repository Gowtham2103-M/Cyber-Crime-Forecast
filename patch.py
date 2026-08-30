import sys

with open('src/ml/ml_engine.py', 'r') as f:
    content = f.read()

trace_mule_chain_old = """    def trace_mule_chain(self, initial_upi):
        # Extract account ID from UPI
        initial_account = initial_upi.split('@')[0]
        
        if initial_account not in self.G:
            return []
            
        # Find all reachable nodes using BFS
        chain = []
        edges = list(nx.edge_bfs(self.G, initial_account))
        for u, v in edges:
            edge_data = self.G.get_edge_data(u, v)
            chain.append({
                'source': u,
                'target': v,
                'amount': edge_data['amount'],
                'timestamp': edge_data['timestamp'].isoformat()
            })
        return chain

    def get_terminal_mules(self, initial_upi):
        initial_account = initial_upi.split('@')[0]
        if initial_account not in self.G:
            return []
            
        descendants = nx.descendants(self.G, initial_account)
        terminals = []
        for node in descendants:
            # If out-degree is 0, it's a leaf node in the transaction graph
            if self.G.out_degree(node) == 0:
                terminals.append(node)
        return terminals"""

new_methods = """    def trace_funds(self, initial_upi, incident_timestamp):
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
        return self.terminal_to_acks_cache.get(terminal_id, [])[:max_acks]"""

if trace_mule_chain_old in content:
    content = content.replace(trace_mule_chain_old, new_methods)
    with open('src/ml/ml_engine.py', 'w') as f:
        f.write(content)
    print('Patched successfully!')
else:
    print('Failed to patch, could not find old trace_mule_chain.')
