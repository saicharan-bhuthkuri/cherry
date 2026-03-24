import os
import joblib
import random
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from data_parser import parse_accident_data

def train_model():
    print("Loading data for training...")
    df = parse_accident_data(r"../CSV .txt")
    
    time_choices = ['Day', 'Night']
    df['time_of_day'] = [random.choice(time_choices) for _ in range(len(df))]

    df['target_risk'] = df['fatalities'] * 3 + df['injuries'] * 1.5 + df['vehicles'] * 0.5
    
    if df['target_risk'].max() > 0:
        df['target_risk'] = (df['target_risk'] / df['target_risk'].max()) * 100
    else:
        df['target_risk'] = 0

    features = ['latitude', 'longitude', 'road_type', 'weather', 'time_of_day']
    X = df[features].copy()
    y = df['target_risk']

    encoders = {}
    for col in ['road_type', 'weather', 'time_of_day']:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        encoders[col] = le
        
    print("Training Random Forest model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    os.makedirs('ml_model_data', exist_ok=True)
    joblib.dump(model, 'ml_model_data/rf_model.joblib')
    joblib.dump(encoders, 'ml_model_data/encoders.joblib')
    
    print("Model and encoders saved to ml_model_data/")

if __name__ == '__main__':
    train_model()
