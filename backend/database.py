from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/saferoute"

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    # Test connection
    with engine.connect() as conn:
        pass
except (OperationalError, Exception):
    # Fallback to SQLite
    engine = create_engine("sqlite:///./saferoute.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

