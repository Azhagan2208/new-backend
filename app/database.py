from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Database Connection
DATABASE_URL = os.getenv("DB_URL")

# If no DB_URL, we don't crash here so the server can at least start
if not DATABASE_URL:
    print("WARNING: No DB_URL found. Database features will fail.")
    # Assigning a dummy URL just to prevent engine creation crash if accessed
    DATABASE_URL = "postgresql://user:pass@localhost/dummy"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
