import os
from dotenv import load_dotenv
from .utils.theme import ThemeManager

# Load environment variables
load_dotenv()

# Configuration - Set via environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.4.170:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# Theme manager instance
theme_manager = ThemeManager()