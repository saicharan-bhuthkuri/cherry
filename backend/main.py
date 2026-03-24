from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import AccidentRecord
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from routing import get_safest_route
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="SafeRoute Peddapalli")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# Load ML components
model_path = 'ml_model_data/rf_model.joblib'
encoder_path = 'ml_model_data/encoders.joblib'

if os.path.exists(model_path) and os.path.exists(encoder_path):
    rf_model = joblib.load(model_path)
    encoders = joblib.load(encoder_path)
else:
    rf_model = None
    encoders = None

class RiskRequest(BaseModel):
    latitude: float
    longitude: float
    road_type: str
    weather: str
    time_of_day: str

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float

@app.get("/accidents")
def get_accidents(db: Session = Depends(get_db)):
    records = db.query(AccidentRecord).all()
    # Serialize for JSON
    res = []
    for r in records:
        res.append({
            "id": r.id, "year": r.year, "mandal": r.mandal,
            "accident_prone_area": r.accident_prone_area,
            "latitude": r.latitude, "longitude": r.longitude,
            "road_type": r.road_type, "vehicles": r.vehicles,
            "fatalities": r.fatalities, "injuries": r.injuries,
            "accident_type": r.accident_type, "weather": r.weather,
            "cause": r.cause, "time_of_day": r.time_of_day
        })
    return res

@app.post("/predict-risk")
def predict_risk(request: RiskRequest):
    if rf_model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    road_type_enc = encode_feature('road_type', request.road_type)
    weather_enc = encode_feature('weather', request.weather)
    time_enc = encode_feature('time_of_day', request.time_of_day)

    df = pd.DataFrame([{
        'latitude': request.latitude,
        'longitude': request.longitude,
        'road_type': road_type_enc,
        'weather': weather_enc,
        'time_of_day': time_enc
    }])

    risk_score = rf_model.predict(df)[0]
    return {"risk_score": float(risk_score)}

def encode_feature(col, val):
    le = encoders[col]
    if val in le.classes_:
        return int(le.transform([val])[0])
    return int(le.transform([le.classes_[0]])[0])

@app.post("/get-route")
def get_route(req: RouteRequest, db: Session = Depends(get_db)):
    if rf_model is None:
        raise HTTPException(status_code=500, detail="Data or model unavailable")
    
    # We pass the db session and model to routing
    # for a fully dynamic predictive routing mapping
    res = get_safest_route(
        req.start_lat, req.start_lon,
        req.end_lat, req.end_lon,
        rf_model, encoders, db
    )
    return res
