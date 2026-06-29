import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GHL_BEARER_TOKEN")
LOCATION_ID = os.getenv("LOCATION_ID")
PIPELINE_ID = os.getenv("PIPELINE_ID")

HEADERS_V3 = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "version": "v3"
}

HEADERS_CONTACTS = {
    "Authorization": f"Bearer {TOKEN}",
    "version": "2023-02-21"
}

BASE = "https://services.leadconnectorhq.com"