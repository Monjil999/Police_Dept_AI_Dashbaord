import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Logging configuration
LOG_LEVEL = logging.INFO

# Database configuration
DATABASE_URL = "sqlite:///police_data.db"

# Cache configuration
CACHE_EXPIRY = 3600  # 1 hour
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# LLM configuration
GROQ_MODEL = "deepseek-r1-distill-llama-70b"
MAX_LLM_RESPONSE_TIME = 10.0  # seconds

# API Keys - now optional and secure
GROQ_API_KEY = os.getenv('GROQ_API_KEY', None)  # No default key for security

# Display configuration
ITEMS_PER_PAGE = 50
MAX_DISPLAY_ROWS = 1000

# Data fetching configuration
DEFAULT_SAMPLE_SIZE = 10000
MAX_DATA_SIZE = 1000000

# Supported file formats
SUPPORTED_FORMATS = ['.csv', '.xlsx', '.json', '.parquet']

# Rate limiting
API_RATE_LIMIT = 100  # requests per minute
DOWNLOAD_TIMEOUT = 300  # 5 minutes

# Security settings
HIDE_SENSITIVE_DATA = True
ALLOW_USER_API_KEYS = True  # Allow users to provide their own API keys

# Data Sources
STANFORD_DATA_URL = "https://openpolicing.stanford.edu/data/"
POLICE_DATA_INITIATIVE_URL = "https://www.policedatainitiative.org/datasets/"

# Cache settings
CACHE_EXPIRY = 3600  # 1 hour in seconds
MAX_CACHE_SIZE = 1000  # Maximum number of cached items

# Performance thresholds
MAX_DASHBOARD_LOAD_TIME = 45  # seconds
MAX_LLM_RESPONSE_TIME = 10   # seconds 