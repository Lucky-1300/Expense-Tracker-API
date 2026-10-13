"""Application configuration settings."""

from pathlib import Path

# Base project directory relative to this config file (independent of terminal cwd)
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory and CSV file path
DATA_DIR = BASE_DIR / "data"
EXPENSES_CSV_PATH = DATA_DIR / "expenses.csv"

# Standard CSV column headers
CSV_HEADERS = ["id", "title", "amount", "category", "date", "notes"]
