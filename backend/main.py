"""
FoodPal Backend Service - FastAPI Application
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from sqlalchemy.orm import Session

from app.database.connection import create_tables, get_db
from app.api.routes import recipes, users, auth, meal_plans
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    try:
        create_tables()
        print("🚀 FoodPal Backend Service started")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("🚀 FoodPal Backend Service started without database")
    yield
    # Shutdown
    print("🛑 FoodPal Backend Service shutting down")


app = FastAPI(
    title="FoodPal API",
    description="Recipe recommendation and meal planning service",
    version="1.0.0", 
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for recipe images
if os.path.exists("../media"):
    app.mount("/media", StaticFiles(directory="../media"), name="media")

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["recipes"])
app.include_router(meal_plans.router, prefix="/api/meal-plans", tags=["meal-plans"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "FoodPal Backend Service", "status": "healthy"}


@app.get("/debug")
async def debug_info():
    """Debug information"""
    import os
    import pwd
    
    try:
        current_user = pwd.getpwuid(os.getuid()).pw_name
    except:
        current_user = "unknown"
    
    return {
        "current_directory": os.getcwd(),
        "user": current_user,
        "uid": os.getuid(),
        "gid": os.getgid(),
        "database_url": settings.DATABASE_URL,
        "tmp_exists": os.path.exists("/tmp"),
        "tmp_writable": os.access("/tmp", os.W_OK),
        "app_exists": os.path.exists("/app"),
        "app_writable": os.access("/app", os.W_OK),
        "files_in_tmp": os.listdir("/tmp") if os.path.exists("/tmp") else "not found",
        "files_in_app": os.listdir("/app") if os.path.exists("/app") else "not found"
    }


@app.post("/init-db")
async def init_database():
    """Manually initialize database"""
    try:
        create_tables()
        return {"status": "success", "message": "Database initialized successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/init-db-simple")
async def init_database_simple():
    """Initialize database with simple SQLite approach"""
    import sqlite3
    import os
    
    try:
        # Try to create a simple SQLite database in /app
        db_path = "/app/foodpal_simple.db"
        conn = sqlite3.connect(db_path)
        
        # Create a simple test table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert a test record
        conn.execute("INSERT INTO test_table (name) VALUES (?)", ("test_user",))
        conn.commit()
        
        # Verify the record
        cursor = conn.execute("SELECT * FROM test_table")
        records = cursor.fetchall()
        
        conn.close()
        
        return {
            "status": "success", 
            "message": f"Simple database created at {db_path}",
            "records": records,
            "file_exists": os.path.exists(db_path),
            "file_size": os.path.getsize(db_path) if os.path.exists(db_path) else 0
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/init-db-sqlalchemy")
async def init_database_sqlalchemy():
    """Initialize database with SQLAlchemy using absolute path"""
    try:
        from sqlalchemy import create_engine, text
        from app.database.models import Base
        
        # Use absolute path
        db_url = "sqlite:////app/foodpal_working.db"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        
        # Test connection first
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
        
        return {
            "status": "success", 
            "message": f"SQLAlchemy database created at {db_url}",
            "tables": tables
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        from app.database.connection import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "foodpal-backend",
        "version": "1.0.0",
        "database": db_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)