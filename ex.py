import os
import requests
import pandas as pd
from dotenv import load_dotenv

# -----------------------------------
# Load environment variables
# -----------------------------------
load_dotenv()

TOKEN = os.getenv("GHL_BEARER_TOKEN")
LOCATION_ID = os.getenv("LOCATION_ID")

if not TOKEN:
    raise ValueError("Missing GHL_BEARER_TOKEN in .env")

if not LOCATION_ID:
    raise ValueError("Missing GHL_LOCATION_ID in .env")

# -----------------------------------
# API Configuration
# -----------------------------------
BASE_URL = "https://services.leadconnectorhq.com"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Version": "2021-07-28",
    "Accept": "application/json",
}

# -----------------------------------
# Get Pipelines
# -----------------------------------
url = f"{BASE_URL}/opportunities/pipelines"

params = {
    "locationId": LOCATION_ID
}

response = requests.get(url, headers=headers, params=params)

response.raise_for_status()

data = response.json()

# -----------------------------------
# Extract pipeline + stage data
# -----------------------------------
rows = []

pipelines = data.get("pipelines", [])

for pipeline in pipelines:
    pipeline_id = pipeline.get("id")
    pipeline_name = pipeline.get("name")

    for stage in pipeline.get("stages", []):
        rows.append({
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline_name,
            "stage_id": stage.get("id"),
            "stage_name": stage.get("name"),
            "stage_position": stage.get("position"),
        })

# -----------------------------------
# Save CSV
# -----------------------------------
df = pd.DataFrame(rows)

df.to_csv("pipelines_and_stages.csv", index=False)

print(df)
print(f"\nSaved {len(df)} stages to pipelines_and_stages.csv")