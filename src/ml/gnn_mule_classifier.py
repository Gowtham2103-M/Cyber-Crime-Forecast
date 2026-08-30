import os
import torch
import torch.nn.functional as F
import pandas as pd
import numpy as np
from torch_geometric.data import Data
from torch_geometric.nn import GATConv
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# 1. Data Parsing & Feature Engineering
def load_data_from_db():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "myuser" in db_url:
        raise ValueError("Valid DATABASE_URL required in .env")
        
    engine = create_engine(db_url)
    print("Fetching data from Postgres...")
    tx_df = pd.read_sql_table('cfcfrms_transactions', engine)
    cashouts_df = pd.read_sql_table('atm_cashouts', engine)
    
    return tx_df, cashouts_df

def build_graph_data(tx_df, cashouts_df):
    print("Engineering Node Features...")
    # Unique accounts
    all_accounts = set(tx_df['source_account']).union(set(tx_df['beneficiary_account']))
    acc_to_idx = {acc: i for i, acc in enumerate(all_accounts)}
    num_nodes = len(all_accounts)
    
    # Inbound stats
    in_stats = tx_df.groupby('beneficiary_account').agg(
        in_degree=('txn_utr', 'count'),
        total_in=('amount', 'sum')
    ).reset_index()
    
    # Outbound stats
    out_stats = tx_df.groupby('source_account').agg(
        out_degree=('txn_utr', 'count'),
        total_out=('amount', 'sum')
    ).reset_index()
    
    # Merge stats
    nodes_df = pd.DataFrame({'account': list(all_accounts)})
    nodes_df = nodes_df.merge(in_stats, left_on='account', right_on='beneficiary_account', how='left')
    nodes_df = nodes_df.merge(out_stats, left_on='account', right_on='source_account', how='left')
    
    # Fill only numeric columns to prevent string dtype TypeError
    num_cols = ['in_degree', 'total_in', 'out_degree', 'total_out']
    nodes_df[num_cols] = nodes_df[num_cols].fillna(0)
    
    # Pass-through ratio (out / in). Handle div by zero by adding epsilon
    nodes_df['pass_through_ratio'] = nodes_df['total_out'] / (nodes_df['total_in'] + 1e-9)
    
    # Node Feature Matrix (X)
    features = ['in_degree', 'out_degree', 'total_in', 'total_out', 'pass_through_ratio']
    X_raw = nodes_df[features].values
    
    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    x_tensor = torch.tensor(X_scaled, dtype=torch.float)
    
    print("Building Edge Index...")
    # Map edges to indices
    src_indices = tx_df['source_account'].map(acc_to_idx).values
    dst_indices = tx_df['beneficiary_account'].map(acc_to_idx).values
    
    edge_index = torch.tensor(np.array([src_indices, dst_indices]), dtype=torch.long)
    
    # Edge attributes (amount and layer_depth)
    edge_attr_raw = tx_df[['amount', 'layer_depth']].values
    edge_attr_scaled = StandardScaler().fit_transform(edge_attr_raw)
    edge_attr = torch.tensor(edge_attr_scaled, dtype=torch.float)
    
    print("Assigning Ground Truth Labels...")
    # Labeling
    mule_accounts_set = set(cashouts_df['mule_account'])
    
    # Ensure order matches acc_to_idx
    y_raw = np.zeros(num_nodes)
    for acc, idx in acc_to_idx.items():
        if acc in mule_accounts_set:
            y_raw[idx] = 1.0
            
    y_tensor = torch.tensor(y_raw, dtype=torch.float).view(-1, 1)
    
    # Masks (80/20 split)
    indices = np.random.permutation(num_nodes)
    split = int(0.8 * num_nodes)
    train_idx = indices[:split]
    test_idx = indices[split:]
    
    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)
    train_mask[train_idx] = True
    test_mask[test_idx] = True
    
    data = Data(x=x_tensor, edge_index=edge_index, edge_attr=edge_attr, y=y_tensor, 
                train_mask=train_mask, test_mask=test_mask)
    
    print(f"Graph built: {data.num_nodes} nodes, {data.num_edges} edges. Mules: {int(y_raw.sum())}")
    return data

# 4. GNN Model Architecture & Training
class GATMuleClassifier(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(GATMuleClassifier, self).__init__()
        # PyG GATConv supports edge attributes optionally, but standard GAT often just uses node features
        # We will use edge attributes in the first layer if edge_dim is specified, but to keep it simple and robust, 
        # we'll just use standard GATConv without edge_attr.
        self.conv1 = GATConv(in_channels, hidden_channels, heads=4, concat=False)
        self.conv2 = GATConv(hidden_channels, out_channels, heads=1, concat=False)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        x = F.dropout(x, p=0.4, training=self.training)
        x = self.conv2(x, edge_index)
        return x

def train_gnn():
    tx_df, cashouts_df = load_data_from_db()
    data = build_graph_data(tx_df, cashouts_df)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    
    model = GATMuleClassifier(in_channels=data.num_node_features, hidden_channels=32, out_channels=1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    
    # Calculate positive weight for highly imbalanced dataset
    num_neg = (data.y[data.train_mask] == 0).sum()
    num_pos = (data.y[data.train_mask] == 1).sum()
    pos_weight = num_neg / (num_pos + 1e-9)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight]).to(device))
    
    print("Training GAT Model...")
    model.train()
    for epoch in range(150):
        optimizer.zero_grad()
        out = model(data.x, data.edge_index)
        loss = criterion(out[data.train_mask], data.y[data.train_mask])
        loss.backward()
        optimizer.step()
        
        if epoch % 30 == 0:
            print(f'Epoch {epoch:>3} | Loss: {loss.item():.4f}')
            
    print("Evaluating Model...")
    model.eval()
    with torch.no_grad():
        out = model(data.x, data.edge_index)
        pred = torch.sigmoid(out[data.test_mask]).cpu().numpy() > 0.5
        y_true = data.y[data.test_mask].cpu().numpy()
        
        acc = accuracy_score(y_true, pred)
        prec = precision_score(y_true, pred, zero_division=0)
        rec = recall_score(y_true, pred, zero_division=0)
        f1 = f1_score(y_true, pred, zero_division=0)
        
        print(f"\nTest Metrics:")
        print(f"Accuracy:  {acc:.4f}")
        print(f"Precision: {prec:.4f}")
        print(f"Recall:    {rec:.4f}")
        print(f"F1-Score:  {f1:.4f}")
        
    os.makedirs('models', exist_ok=True)
    torch.save(model.state_dict(), 'models/gnn_mule_model.pth')
    print("Model saved to models/gnn_mule_model.pth")

if __name__ == "__main__":
    train_gnn()
