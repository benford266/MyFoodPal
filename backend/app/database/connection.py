"""
Database Connection and Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ..config import settings
from .models import Base


# Create database engine
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency to get database session
    
    Returns:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    import os
    
    # Ensure database directory exists
    db_path = settings.DATABASE_URL.replace('sqlite:///', '')
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"📁 Created database directory: {db_dir}")
    
    # Make sure the tmp directory is writable
    if not os.access(db_dir or '.', os.W_OK):
        print(f"⚠️ Warning: Directory {db_dir or '.'} is not writable")
    
    try:
        # Test connection first
        with engine.connect() as conn:
            print("🔗 Database connection test successful")
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Verify table creation
        with engine.connect() as conn:
            result = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in result]
            print(f"📋 Created tables: {', '.join(tables)}")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        print(f"📍 Database path: {db_path}")
        print(f"📁 Database directory: {db_dir}")
        raise