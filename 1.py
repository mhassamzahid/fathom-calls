import pandas as pd

# -----------------------------
# Files
# -----------------------------
PIPELINE_FILE = "pipeline_by_stage_and_age.csv"
STAGES_FILE = "pipelines_and_stages.csv"
OUTPUT_FILE = "stage_age_summary.csv"

# -----------------------------
# Load data
# -----------------------------
opps = pd.read_csv(PIPELINE_FILE)
stages = pd.read_csv(STAGES_FILE)

# Ensure age is numeric
opps["age_days"] = pd.to_numeric(opps["age_days"], errors="coerce").fillna(0)

# -----------------------------
# Merge stage information
# -----------------------------
opps = opps.merge(
    stages[
        [
            "pipeline_id",
            "pipeline_name",
            "stage_id",
            "stage_name",
            "stage_position",
        ]
    ],
    left_on=["pipeline_id", "pipeline_stage_id"],
    right_on=["pipeline_id", "stage_id"],
    how="left",
)

# -----------------------------
# Summarize by stage
# -----------------------------
summary = (
    opps.groupby(
        [
            "pipeline_id",
            "pipeline_name",
            "pipeline_stage_id",
            "stage_name",
            "stage_position",
        ],
        dropna=False,
        as_index=False,
    )
    .agg(
        Total_Opportunities=("opportunity_id", "count"),
        Over_30_Days=("age_days", lambda x: (x > 30).sum()),
        Over_60_Days=("age_days", lambda x: (x > 60).sum()),
        Over_90_Days=("age_days", lambda x: (x > 90).sum()),
        Avg_Age=("age_days", "mean"),
        Max_Age=("age_days", "max"),
    )
)

summary["Avg_Age"] = summary["Avg_Age"].round(1)

# -----------------------------
# Sort nicely
# -----------------------------
summary = summary.sort_values(
    ["pipeline_name", "stage_position"]
)

# -----------------------------
# Save
# -----------------------------
summary.to_csv(OUTPUT_FILE, index=False)

print(f"Saved {OUTPUT_FILE}")
print(summary)