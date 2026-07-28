import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
LOGS_DIR = BASE_DIR / 'logs'

# Ensure directories exist
for directory in [RAW_DIR / 'ohlcv', RAW_DIR / 'financials', RAW_DIR / 'cstc', RAW_DIR / 'universe', PROCESSED_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / '.env')

# Yuanta API Configurations
YUANTA_BASE_URL = "https://ysradarapi.yuanta.com.vn/api/v3"

# Chunking/Batching Settings
API_CHUNK_SIZE = 50   # Number of tickers to query in a single batch
API_TIMEOUT = 10      # Timeout in seconds
API_MAX_RETRIES = 3   # Max retries for API requests
