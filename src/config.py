import os
from dotenv import load_dotenv
from .utils.improved_theme import get_improved_theme_manager

# Load environment variables
load_dotenv()

# Configuration - Set via environment variables
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://192.168.4.208:1234")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "qwen/qwen3-4b")

# Theme manager instance
theme_manager = get_improved_theme_manager()