import os
from dotenv import load_dotenv

load_dotenv()

# API Keys

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Paths

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler\Library\bin"

# Output Directories

OUTPUT_DIR = "project_output"  # For user results and OCR text
CACHE_DIR = "vehicle_cache"   # For API responses
LOG_DIR = "logs"              # For processing logs

# Create directories

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# API Settings

VEHICLE_API_BASE_URL = "https://car-api2.p.rapidapi.com/api/vin/"
VEHICLE_API_HOST = "car-api2.p.rapidapi.com"

# App Settings

APP_HOST = "0.0.0.0"
APP_PORT = 8000
MAX_FILE_SIZE = 10 * 1024 * 1024

# Analysis Settings

RISK_THRESHOLD_HIGH = 70  # Score above this is good
RISK_THRESHOLD_LOW = 40   # Score below this is poor
CACHE_EXPIRY_DAYS = 7

# Set to True to force API refresh (comment out to use cache)
FORCE_API_REFRESH = False

# Additional vehicle APIs (optional)
EDMUNDS_API_KEY = os.getenv("EDMUNDS_API_KEY", "")
KBB_API_KEY = os.getenv("KBB_API_KEY", "")
