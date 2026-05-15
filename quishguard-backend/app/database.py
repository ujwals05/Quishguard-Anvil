from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

# Create engine based on DB type
if "sqlite" in settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,   # test connections before use (handles Supabase idle timeouts)
        pool_size=5,          # keep at most 5 persistent connections
        max_overflow=10,      # allow up to 10 extra connections under load
        pool_recycle=1800,    # recycle connections every 30 min
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Called on server startup — creates all tables if they don't exist."""
    from app.models import threat

    # Import more models here later if needed
    # from app.models import email_event

    Base.metadata.create_all(bind=engine)