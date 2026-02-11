from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Database Connection
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Construct the SQLAlchemy connection string
if all([USER, PASSWORD, HOST, PORT, DBNAME]):
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
else:
    # Fallback to DB_URL if individual variables are missing (for backward compatibility or local dev)
    DATABASE_URL = os.getenv("DB_URL")

if not DATABASE_URL:
    raise ValueError(
        "No database configuration found in environment variables. Please check your .env file."
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
