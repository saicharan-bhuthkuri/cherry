from sqlalchemy import Column, Integer, Float, String
from database import Base

class AccidentRecord(Base):
    __tablename__ = "accidents"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer)
    mandal = Column(String)
    accident_prone_area = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    road_type = Column(String)
    vehicles = Column(Integer)
    fatalities = Column(Integer)
    injuries = Column(Integer)
    accident_type = Column(String)
    weather = Column(String)
    cause = Column(String)
    # Synthesized feature for time
    time_of_day = Column(String)
