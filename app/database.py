from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Use single DATABASE_URL from Vercel environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables.")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"}  # Required for Supabase
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
