import numpy as np
import json

def calculate_rossmo_surface(cashout_coords, resolution=50, B=0.02, f=1.2, g=1.2):
    """
    Vectorized implementation of Rossmo's Formula using NumPy.
    cashout_coords: list of (latitude, longitude)
    B: Buffer zone (in degrees)
    f, g: Empirical decay exponents
    """
    coords = np.array(cashout_coords)
    if len(coords) < 1:
        return None, None, None
        
    lats = coords[:, 0]
    lons = coords[:, 1]
    
    # 1. Geographic Bounding Box with padding
    pad = 0.05
    min_lat, max_lat = lats.min() - pad, lats.max() + pad
    min_lon, max_lon = lons.min() - pad, lons.max() + pad
    
    # 2. Generate 2D meshgrid
    lat_space = np.linspace(min_lat, max_lat, resolution)
    lon_space = np.linspace(min_lon, max_lon, resolution)
    LON, LAT = np.meshgrid(lon_space, lat_space)
    
    total_scores = np.zeros_like(LAT)
    
    # 3 & 4. Calculate distances and apply Rossmo's equation simultaneously
    for c_lat, c_lon in coords:
        # Manhattan distance approximation in degrees
        dist = np.abs(LAT - c_lat) + np.abs(LON - c_lon)
        dist = np.clip(dist, 1e-6, None) # Prevent div by zero
        
        # Boolean masks
        mask_outside = dist > B
        mask_inside = dist <= B
        
        # Calculate components
        score_c = np.zeros_like(dist)
        
        # Distance decay (outside buffer)
        score_c[mask_outside] = 1.0 / (dist[mask_outside] ** f)
        
        # Buffer decay (inside buffer)
        # B^(g-f) / (2B - dist)^g
        b_term = B ** (g - f)
        denom = (2 * B - dist[mask_inside]) ** g
        score_c[mask_inside] = b_term / denom
        
        # Accumulate
        total_scores += score_c
        
    # 5. Normalize
    max_score = total_scores.max()
    if max_score > 0:
        total_scores = total_scores / max_score
        
    return lat_space, lon_space, total_scores

def generate_geojson_grid(lat_space, lon_space, scores, threshold=0.2):
    """
    Converts the NumPy grid into a GeoJSON FeatureCollection of Polygons.
    """
    if scores is None:
        return {"type": "FeatureCollection", "features": []}
        
    features = []
    
    # Grid cell dimensions
    d_lat = lat_space[1] - lat_space[0]
    d_lon = lon_space[1] - lon_space[0]
    
    rows, cols = scores.shape
    for i in range(rows - 1):
        for j in range(cols - 1):
            score = float(scores[i, j])
            if score < threshold:
                continue
                
            # Create polygon coordinates (bottom-left, bottom-right, top-right, top-left, close)
            # GeoJSON uses [longitude, latitude]
            lat1, lon1 = lat_space[i], lon_space[j]
            lat2, lon2 = lat_space[i+1], lon_space[j+1]
            
            polygon = [
                [lon1, lat1],
                [lon2, lat1],
                [lon2, lat2],
                [lon1, lat2],
                [lon1, lat1]
            ]
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [polygon]
                },
                "properties": {
                    "jeopardy_score": score
                }
            }
            features.append(feature)
            
    return {
        "type": "FeatureCollection",
        "features": features
    }
