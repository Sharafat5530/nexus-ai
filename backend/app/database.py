import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.config import settings

logger = logging.getLogger("nexus.database")

try:
    if settings.DATABASE_URL.startswith("postgresql"):
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3}
        )
        with engine.connect() as conn:
            pass
        logger.info("Connected to PostgreSQL database.")
    else:
        engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
except Exception as e:
    logger.warning(
        f"PostgreSQL connection to {settings.DATABASE_URL} failed ({e}). "
        "Falling back to local SQLite (nexus_dev.db) for zero-config local development."
    )
    fallback_url = "sqlite:///./nexus_dev.db"
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
