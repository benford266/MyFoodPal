from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import threading
from contextlib import contextmanager
from .models import Base

# Database setup with optimized connection pooling
DATABASE_URL = "sqlite:///./foodpal.db"

# Configure engine with connection pooling and WAL mode for better concurrency
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30,  # 30 second timeout for busy database
    },
    poolclass=StaticPool,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
    echo=False  # Set to True for SQL debugging
)

# Enable WAL mode for better concurrency
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance and concurrency"""
    cursor = dbapi_connection.cursor()
    # WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")
    # Reduce synchronous for better performance (still safe in WAL mode)
    cursor.execute("PRAGMA synchronous=NORMAL")
    # Increase cache size to 64MB
    cursor.execute("PRAGMA cache_size=-64000")
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
)

def get_db():
    """Get database session with proper error handling"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        try:
            db.close()
        except Exception as e:
            print(f"Error closing database session: {e}")

@contextmanager
def get_db_context():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database transaction failed: {e}")
        raise
    finally:
        try:
            db.close()
        except Exception as e:
            print(f"Error closing database session: {e}")

# Thread-local storage for database sessions
_local = threading.local()

def get_thread_local_db():
    """Get thread-local database session for UI operations"""
    if not hasattr(_local, 'db'):
        _local.db = SessionLocal()
    return _local.db

def close_thread_local_db():
    """Close thread-local database session"""
    if hasattr(_local, 'db'):
        try:
            _local.db.close()
            delattr(_local, 'db')
        except Exception as e:
            print(f"Error closing thread-local database session: {e}")

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)