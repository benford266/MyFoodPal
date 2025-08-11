from fastapi import FastAPI
from nicegui import ui, app
from datetime import datetime
import os
import logging

# Setup logging first
from src.utils.logging_config import setup_logging, get_logger
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    enable_file_logging=os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
)

logger = get_logger('main')

# Import database setup
from src.database.connection import create_tables
from src.database.models import User

# Import API endpoints
from src.api.endpoints import setup_api_routes

# Import UI pages (this will register all the routes)
from src.ui import pages

# Import configuration
from src.config import LM_STUDIO_BASE_URL, LM_STUDIO_MODEL

# FastAPI app with proper exception handling
fastapi_app = FastAPI(
    title="FoodPal API",
    description="Backend API for FoodPal recipe generation",
    version="1.0.0"
)

try:
    # Setup API routes
    setup_api_routes(fastapi_app)
    logger.info("API routes configured successfully")
    
    # Initialize database
    create_tables()
    logger.info("Database tables initialized successfully")
    
    # Serve static media files with proper error handling
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    
    # Ensure media directory exists
    MEDIA_DIR = Path("media")
    MEDIA_DIR.mkdir(exist_ok=True)
    
    # Mount static files with proper path resolution
    try:
        app.mount("/media", StaticFiles(directory=str(MEDIA_DIR.absolute())), name="media")
        logger.info(f"Media directory mounted: {MEDIA_DIR.absolute()}")
    except Exception as e:
        logger.error(f"Failed to mount media directory: {e}")
        # Create fallback handler for missing media
        @fastapi_app.get("/media/{file_path:path}")
        async def fallback_media(file_path: str):
            logger.warning(f"Media fallback triggered for: {file_path}")
            return {"error": "Media service unavailable"}
    
    # Configure NiceGUI
    app.mount('/api', fastapi_app)
    logger.info("NiceGUI configured with FastAPI integration")
    
except Exception as e:
    logger.critical(f"Critical error during application startup: {e}")
    raise

if __name__ in {"__main__", "__mp_main__"}:
    # Generate or use a storage secret for session management
    storage_secret = os.getenv("NICEGUI_STORAGE_SECRET", "foodpal-secret-key-2024-change-in-production")
    port = int(os.getenv("PORT", 8080))
    
    logger.info(f"Starting FoodPal server on port {port}")
    logger.info(f"LM Studio URL: {LM_STUDIO_BASE_URL}")
    logger.info(f"LM Studio Model: {LM_STUDIO_MODEL}")
    
    try:
        ui.run(
            port=port, 
            title="MyFoodPal Recipe Generator", 
            storage_secret=storage_secret,
            show=False,  # Don't auto-open browser in production
            reload=False  # Disable auto-reload in production
        )
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
        raise