from fastapi import FastAPI
from nicegui import ui, app
from datetime import datetime
import os

# Import database setup
from src.database.connection import create_tables
from src.database.models import User

# Import API endpoints
from src.api.endpoints import setup_api_routes

# Import UI pages (this will register all the routes)
from src.ui import pages

# Import configuration
from src.config import LM_STUDIO_BASE_URL, LM_STUDIO_MODEL

# FastAPI app
fastapi_app = FastAPI()

# Setup API routes
setup_api_routes(fastapi_app)

# Initialize database
create_tables()

# Serve static media files
from fastapi.staticfiles import StaticFiles
app.mount("/media", StaticFiles(directory="media"), name="media")

# Configure NiceGUI
app.mount('/api', fastapi_app)

if __name__ in {"__main__", "__mp_main__"}:
    # Generate or use a storage secret for session management
    storage_secret = os.getenv("NICEGUI_STORAGE_SECRET", "foodpal-secret-key-2024-change-in-production")
    ui.run(port=8080, title="FoodPal Recipe Generator", storage_secret=storage_secret)