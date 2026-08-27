import sys
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from typing import Optional

# Add src to path to import ml_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.ml_engine import MLEngine

app = FastAPI(
    title="Proactive Cybercrime Intervention API",
    description="Predictive Analytics Engine for I4C",
    version="1.0.0"
)

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
    
    mule_chain = ml_engine.trace_mule_chain(comp_details['initial_beneficiary_upi'])
    hotspots = ml_engine.predict_hotspots(comp_details, time_horizon_hours=2, top_k=5)
    
    return {
        "complaint_details": comp_details,
        "mule_chain": mule_chain,
        "predicted_hotspots": hotspots
    }

@app.get("/api/v1/analytics/risk-heatmap")
def get_risk_heatmap(state: Optional[str] = None, time_horizon_hours: int = 2):
    """
    Generates a GeoJSON FeatureCollection of all ATMs with their current
    computed dynamic risk intensity for direct map visualization.
    """
    # For a global heatmap, simulate current time as the latest complaint in DB
    current_time = ml_engine.complaints_df['reported_timestamp'].max()
    
    dummy_comp = {
        'reported_timestamp': current_time,
        'defrauded_amount': 0
    }
    
    # Predict for all ATMS
    all_hotspots = ml_engine.predict_hotspots(dummy_comp, time_horizon_hours=time_horizon_hours, top_k=len(ml_engine.unique_atms))
    
    features = []
    for h in all_hotspots:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [h["longitude"], h["latitude"]]
            },
            "properties": {
                "terminal_id": h["terminal_id"],
                "risk_intensity": h["risk_score"]
            }
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

@app.get("/api/v1/alerts/active")
def get_active_alerts():
    """
    Returns a stream of high-priority alerts where risk score > 0.85
    requiring immediate police dispatch or bank freezing.
    """
    current_time = ml_engine.complaints_df['reported_timestamp'].max()
    dummy_comp = {
        'reported_timestamp': current_time,
        'defrauded_amount': 0
    }
    
    all_hotspots = ml_engine.predict_hotspots(dummy_comp, time_horizon_hours=1, top_k=100)
    
    # Filter for high risk
    alerts = [h for h in all_hotspots if h["risk_score"] > 0.85]
    
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
