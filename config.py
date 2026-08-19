# config.py

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN")
GOOGLE_SHEET_ID   = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDS_PATH = os.getenv("GOOGLE_CREDS_PATH", "./credentials.json")
PERIOD_DAYS       = int(os.getenv("PERIOD_DAYS", 7))
GITHUB_ORG        = os.getenv("GITHUB_ORG")

