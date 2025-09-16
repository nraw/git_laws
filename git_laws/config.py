"""
Configuration file for the git_laws project.
Centralized settings and paths to avoid hardcoding.
"""

import os

# Base project directory (automatically detected)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data paths
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MINISTERS_DIR = os.path.join(DATA_DIR, "ministers")
MINISTERS_COMBINED_FILE = os.path.join(DATA_DIR, "ministers_combined.json")

# Output paths
GIT_LAWS_DIR = os.path.dirname(__file__)  # This git_laws/ directory

# Data sources
GOVERNMENT_BASE_URL = "https://www.gov.si/drzavni-organi/vlada/o-vladi/pretekle-vlade/"

# File patterns
GOVERNMENT_FILE_PATTERN = "government_*.json"

# Default settings
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ["en", "sl"]

# Logging settings
LOG_LEVEL = "INFO"