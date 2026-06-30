import pandas as pd

# -----------------------------
# Configuration
# -----------------------------
INPUT_FILE = "pipeline_by_stage_and_age.csv"
OUTPUT_FILE = "pipeline_stage_summary.csv"

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv(INPUT_FILE)

# -----------------------------
# Ensure correct data types
# -----------------------------
df["monetary_value"] = pd.to_numeric(df["monetary_value"], errors="coerce").fillna(0)
df["age_days"] = pd.to_numeric(df["age_days"], errors="coerce")

# -----------------------------
# Group by stage
# -----------------------------
summary = (
    df.groupby("pipeline_stage_id")
    .agg(
        Opportunities=("opportunity_id", "count"),
        Pipeline_Value=("monetary_value", "sum"),
        Avg_Age=("age_days", "mean"),
    )
    .reset_index()
)

# -----------------------------
# Rename columns
# -----------------------------
summary.rename(columns={"pipeline_stage_id": "Stage"}, inplace=True)

# Round average age
summary["Avg_Age"] = summary["Avg_Age"].round(1)

# Optional: Round pipeline value to 2 decimals
summary["Pipeline_Value"] = summary["Pipeline_Value"].round(2)

# -----------------------------
# Save
# -----------------------------
summary.to_csv(OUTPUT_FILE, index=False)

print(f"Saved summary to {OUTPUT_FILE}")
print(summary)