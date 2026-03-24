import math
import heapq
from sqlalchemy.orm import Session
from models import AccidentRecord
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_safest_route(start_lat, start_lon, end_lat, end_lon, rf_model, encoders, db: Session):
    # Simulated Routing Graph:
    # Build nodes from accident locations + user start/end
    records = db.query(AccidentRecord).all()
    nodes = [{'id': 'start', 'lat': start_lat, 'lon': start_lon, 'risk': 0.0}]
    
    for idx, r in enumerate(records):
        nodes.append({'id': str(r.id), 'lat': r.latitude, 'lon': r.longitude})
        
    nodes.append({'id': 'end', 'lat': end_lat, 'lon': end_lon, 'risk': 0.0})

    # Calculate model risk at each node (simulate weather=clear, time=Day for current condition)
    # Ideally they'd be passed in req, but sticking to defaults for graph edge weight derivation
    df_nodes = pd.DataFrame([{
        'latitude': n['lat'], 'longitude': n['lon'],
        'road_type': encoders['road_type'].transform(['highway' if 'highway' in encoders['road_type'].classes_ else encoders['road_type'].classes_[0]])[0],
        'weather': encoders['weather'].transform(['clear' if 'clear' in encoders['weather'].classes_ else encoders['weather'].classes_[0]])[0],
        'time_of_day': encoders['time_of_day'].transform(['Day' if 'Day' in encoders['time_of_day'].classes_ else encoders['time_of_day'].classes_[0]])[0]
    } for n in nodes[1:-1]]) # skip start/end risk
    
    if not df_nodes.empty and rf_model:
        risks = rf_model.predict(df_nodes)
        for i, r in enumerate(risks):
            nodes[i+1]['risk'] = r
            
    # Connect nearby nodes to form a graph
    adj = {n['id']: [] for n in nodes}
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            d = haversine(nodes[i]['lat'], nodes[i]['lon'], nodes[j]['lat'], nodes[j]['lon'])
            if d < 5.0 or nodes[i]['id'] in ['start', 'end'] or nodes[j]['id'] in ['start', 'end']: # connect if within 5km or source/sink
                # cost = distance + normalized_risk * penalty
                risk_i = nodes[i].get('risk', 0)
                risk_j = nodes[j].get('risk', 0)
                avg_risk = (risk_i + risk_j) / 2
                
                safe_cost = d + (avg_risk * 0.1)  # safe cost heavily penalizes risk
                short_cost = d
                
                adj[nodes[i]['id']].append((nodes[j]['id'], safe_cost, short_cost, avg_risk))
                adj[nodes[j]['id']].append((nodes[i]['id'], safe_cost, short_cost, avg_risk))

    def astar(cost_idx=1): # 1 for safe_cost, 2 for short_cost
        pq = [(0.0, 'start', [])] # type: ignore
        visited = set()
        while pq:
            curr_cost, curr_id, path = heapq.heappop(pq)
            if curr_id in visited:
                continue
            visited.add(curr_id)
            path = path + [curr_id]
            if curr_id == 'end':
                return path, curr_cost
                
            for nxt_id, safe_c, short_c, avg_risk in adj[curr_id]:
                if nxt_id not in visited:
                    cost = safe_c if cost_idx == 1 else short_c
                    heapq.heappush(pq, (curr_cost + cost, nxt_id, path))
        return [], float('inf')

    safe_path, safe_score = astar(1)
    short_path, short_score = astar(2)

    node_map = {n['id']: {'lat': n['lat'], 'lon': n['lon'], 'risk': n.get('risk', 0)} for n in nodes}
    
    return {
        "safest_route": [node_map[n] for n in safe_path],
        "shortest_route": [node_map[n] for n in short_path],
        "safe_score": safe_score,
        "short_score": short_score
    }
