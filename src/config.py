import os
from dotenv import load_dotenv
from .utils.theme import ThemeManager

# Load environment variables
load_dotenv()

# Configuration - Set via environment variables
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "llama-3.1-8b-instruct")

# Theme manager instance
theme_manager = ThemeManager()