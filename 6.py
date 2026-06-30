import pandas as pd

# -----------------------------
# Load opportunities
# -----------------------------
INPUT_FILE = "opportunities.csv"
OUTPUT_FILE = "pipeline_by_stage_and_age.csv"

df = pd.read_csv(INPUT_FILE)

# -----------------------------
# Parse dates
# -----------------------------
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

# -----------------------------
# Keep only open opportunities
# -----------------------------
df = df[df["status"].str.lower() == "open"].copy()

# -----------------------------
# Calculate age
# -----------------------------
today = pd.Timestamp.now(tz="UTC")

df["age_days"] = (
    today - df["created_at"]
).dt.days

# -----------------------------
# Age buckets
# -----------------------------
def bucket(days):
    if pd.isna(days):
        return "Unknown"
    elif days <= 30:
        return "0-30"
    elif days <= 60:
        return "31-60"
    elif days <= 90:
        return "61-90"
    else:
        return "90+"

df["age_bucket"] = df["age_days"].apply(bucket)

# -----------------------------
# Keep useful columns
# -----------------------------
output = df[
    [
        "opportunity_id",
        "contact_name",
        "pipeline_id",
        "pipeline_stage_id",
        "monetary_value",
        "created_at",
        "age_days",
        "age_bucket",
    ]
]

# -----------------------------
# Save
# -----------------------------
output.to_csv(OUTPUT_FILE, index=False)

print(f"Saved {len(output)} opportunities to {OUTPUT_FILE}")