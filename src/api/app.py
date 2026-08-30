import sys
import os
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from typing import Optional, List

# Add src to path to import ml_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.ml_engine import MLEngine
from ml.rossmo_profiling import calculate_rossmo_surface, generate_geojson_grid
from api.auth import auth_router, get_current_user

app = FastAPI(
    title="Proactive Cybercrime Intervention API",
    description="Predictive Analytics Engine for I4C",
    version="1.0.0"
)

app.include_router(auth_router)

# Enable CORS for local Vite/React testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Booting ML Engine & Loading Graph...")
ml_engine = MLEngine()
print("App ready to serve requests.")

class ComplaintRequest(BaseModel):
    ack_no: str

@app.post("/api/v1/predict/complaint")
def predict_complaint(req: ComplaintRequest):
    """
    Given a complaint ACK number, traces the funds through the mule network
    and predicts the top likely ATM withdrawal hotspots.
    """
    comp_details = ml_engine.get_complaint_details(req.ack_no)
    if not comp_details:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    # Format dates for JSON
    comp_details['incident_timestamp'] = comp_details['incident_timestamp'].isoformat()
    comp_details['reported_timestamp'] = comp_details['reported_timestamp'].isoformat()
    
    mule_chain_data = ml_engine.trace_mule_chain(comp_details['initial_beneficiary_upi'], comp_details['incident_timestamp'])
    hotspots = ml_engine.predict_hotspots(comp_details, time_horizon_hours=2, top_k=5)
    
    return {
        "complaint_details": comp_details,
        "mule_chain": mule_chain_data.get("edges", []),
        "flagged_nodes": mule_chain_data.get("flagged_nodes", []),
        "predicted_hotspots": hotspots
    }

class NewComplaint(BaseModel):
    crime_category: str
    defrauded_amount: float
    initial_beneficiary_upi: str
    victim_state: str
    aadhar_number: str
    phone_number: str

@app.post("/api/v1/complaints")
def submit_complaint(comp: NewComplaint):
    """Public endpoint to register a new cybercrime complaint"""
    import random
    from datetime import datetime
    import psycopg2
    
    ack_no = f"314{random.randint(10000000000, 99999999999)}"
    now = datetime.utcnow()
    
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ncrp_complaints 
        (ack_no, incident_timestamp, reported_timestamp, crime_category, defrauded_amount, initial_beneficiary_upi, victim_state, aadhar_number, phone_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (ack_no, now, now, comp.crime_category, comp.defrauded_amount, comp.initial_beneficiary_upi, comp.victim_state, comp.aadhar_number, comp.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    
    # Refresh ML Engine cache
    ml_engine.load_data()
    return {"ack_no": ack_no, "message": "Complaint registered successfully."}

class TriangulateRequest(BaseModel):
    terminal_ids: List[str]

@app.post("/api/v1/strategic/triangulate")
def triangulate_syndicate(req: TriangulateRequest):
    """
    Applies Rossmo's Formula to predict the anchor point/hideout of the 
    criminal syndicate based on their historical ATM cashout locations.
    """
    if not req.terminal_ids or len(req.terminal_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 terminals to triangulate accurately.")
        
    # Get lat/lon for these terminals
    df = ml_engine.unique_atms
    target_atms = df[df['terminal_id'].isin(req.terminal_ids)]
    
    if target_atms.empty:
        raise HTTPException(status_code=404, detail="Terminals not found.")
        
    coords = target_atms[['latitude', 'longitude']].values.tolist()
    
    from sklearn.cluster import DBSCAN
    import numpy as np
    
    # Cluster ATMs that are >1.0 degree (~110km) apart so isolated outliers get their own grid
    clustering = DBSCAN(eps=1.0, min_samples=1).fit(coords)
    
    all_features = []
    for cluster_id in set(clustering.labels_):
        cluster_coords = [coords[i] for i in range(len(coords)) if clustering.labels_[i] == cluster_id]
        
        # Run Rossmo profiling (B=0.015 is approx 1.5km buffer)
        lat_space, lon_space, scores = calculate_rossmo_surface(cluster_coords, resolution=60, B=0.015)
        grid = generate_geojson_grid(lat_space, lon_space, scores, threshold=0.2)
        all_features.extend(grid.get("features", []))
        
    return {"type": "FeatureCollection", "features": all_features}

def filter_by_jurisdiction(hotspots, user):
    if user.get('role') != 'officer' or not user.get('station_lat'):
        return hotspots
    lat, lon = user['station_lat'], user['station_lon']
    # 0.5 degrees Euclidean is roughly 55km radius
    return [h for h in hotspots if ((h['latitude'] - lat)**2 + (h['longitude'] - lon)**2)**0.5 < 0.5]

@app.get("/api/v1/analytics/risk-heatmap")
def get_risk_heatmap(state: Optional[str] = None, time_horizon_hours: int = 2, current_user: dict = Depends(get_current_user)):
    """
    Generates a GeoJSON FeatureCollection of ATMs with risk intensity.
    Filters by jurisdiction if user is an officer.
    """
    current_time = ml_engine.complaints_df['reported_timestamp'].max()
    dummy_comp = {'reported_timestamp': current_time, 'defrauded_amount': 0}
    
    all_hotspots = ml_engine.predict_hotspots(dummy_comp, time_horizon_hours=time_horizon_hours, top_k=len(ml_engine.unique_atms))
    all_hotspots = filter_by_jurisdiction(all_hotspots, current_user)
    
    features = []
    for h in all_hotspots:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [h["longitude"], h["latitude"]]},
            "properties": {"terminal_id": h["terminal_id"], "risk_intensity": h["risk_score"]}
        })
    return {"type": "FeatureCollection", "features": features}

@app.get("/api/v1/alerts/active")
def get_active_alerts(current_user: dict = Depends(get_current_user)):
    """
    Returns a stream of high-priority alerts where risk score > 0.85,
    along with the likely ACK IDs associated with the terminal.
    """
    current_time = ml_engine.complaints_df['reported_timestamp'].max()
    dummy_comp = {'reported_timestamp': current_time, 'defrauded_amount': 0}
    
    # Get ALL ATMs without top_k truncation, so smaller jurisdictions aren't excluded by Jamtara's sheer volume
    all_hotspots = ml_engine.predict_hotspots(dummy_comp, time_horizon_hours=1, top_k=len(ml_engine.unique_atms))
    
    valid_alerts = []
    for alert in all_hotspots:
        acks = ml_engine.get_acks_for_terminal(alert['terminal_id'])
        if acks:
            alert['associated_acks'] = acks
            valid_alerts.append(alert)
            
    if current_user.get('role') == 'officer':
        local_hotspots = filter_by_jurisdiction(valid_alerts, current_user)
        alerts = local_hotspots[:15]
        
        # Re-normalize locally so the highest risk ATM in their jurisdiction shows as 100% relative risk
        if alerts and alerts[0]['risk_score'] > 0:
            local_max = alerts[0]['risk_score']
            for a in alerts:
                a['risk_score'] = min(1.0, a['risk_score'] / local_max)
    else:
        # Admins see globally diverse critical alerts (avoid clustering all 20 in Jamtara)
        alerts = []
        for h in valid_alerts:
            if h["risk_score"] > 0.85:
                # Enforce ~55km diversity radius
                is_far = True
                for a in alerts:
                    dist = ((h['latitude'] - a['latitude'])**2 + (h['longitude'] - a['longitude'])**2)**0.5
                    if dist < 0.5:
                        is_far = False
                        break
                if is_far:
                    alerts.append(h)
                if len(alerts) >= 15:
                    break
        
    return alerts

@app.get("/api/v1/analytics/stats")
def get_global_stats():
    """
    Returns global statistics for the dashboard.
    """
    complaints = ml_engine.complaints_df
    
    total_complaints = len(complaints)
    total_defrauded = complaints['defrauded_amount'].sum()
    
    top_victim_states = complaints['victim_state'].value_counts().head(5).to_dict()
    
    # We can group by terminal type in cashouts
    cashouts = ml_engine.cashouts_df
    top_terminals = cashouts['terminal_type'].value_counts().head(3).to_dict()
    
    # Let's also do top crime categories
    top_crimes = complaints['crime_category'].value_counts().head(4).to_dict()
    
    return {
        "total_complaints": total_complaints,
        "total_defrauded_amount": total_defrauded,
        "top_victim_states": top_victim_states,
        "top_cashout_terminals": top_terminals,
        "top_crimes": top_crimes
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
