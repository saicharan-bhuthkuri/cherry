from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import AccidentRecord
from sqlalchemy.exc import OperationalError
import random
from data_parser import parse_accident_data

# Recreate tables
try:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
except OperationalError as e:
    print(f"Failed to connect to PostgreSQL. Please ensure it is running and 'saferoute' db exists. Error: {e}")
    # Fallback to SQLite
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///./saferoute.db", connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionLocal.configure(bind=engine)

def load_data():
    df = parse_accident_data(r"../CSV .txt")
    time_choices = ['Day', 'Night']
    
    db: Session = SessionLocal()
    records = []
    
    for _, row in df.iterrows():
        record = AccidentRecord(
            year=row.get('year'),
            mandal=row.get('mandal'),
            accident_prone_area=row.get('accident_prone_area'),
            latitude=row.get('latitude'),
            longitude=row.get('longitude'),
            road_type=row.get('road_type'),
            vehicles=row.get('vehicles'),
            fatalities=row.get('fatalities'),
            injuries=row.get('injuries'),
            accident_type=row.get('accident_type'),
            weather=row.get('weather'),
            cause=row.get('cause'),
            time_of_day=random.choice(time_choices)
        )
        records.append(record)
    
    db.add_all(records)
    db.commit()
    print(f"Loaded {len(records)} records into the database.")

if __name__ == "__main__":
    load_data()
