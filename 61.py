import pandas as pd

# Input files
PIPELINE_FILE = "pipeline_by_stage_and_age.csv"
STAGES_FILE = "pipelines_and_stages.csv"

# Output file
OUTPUT_FILE = "pipeline_stage_quarterly.csv"

# -----------------------
# Read files
# -----------------------
df = pd.read_csv(PIPELINE_FILE)
stages = pd.read_csv(STAGES_FILE)

# Parse dates
df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

# Quarter (e.g. 2025-Q2)
df["Quarter"] = (
    df["created_at"].dt.year.astype(str)
    + "-Q"
    + df["created_at"].dt.quarter.astype(str)
)

# -----------------------
# Quarterly aggregation
# -----------------------
summary = (
    df.groupby(
        ["Quarter", "pipeline_id", "pipeline_stage_id"],
        as_index=False
    )
    .agg(
        Opportunities=("opportunity_id", "count"),
        Pipeline_Value=("monetary_value", "sum"),
        Avg_Age=("age_days", "mean"),
    )
)

summary["Avg_Age"] = summary["Avg_Age"].round(1)

# -----------------------
# Merge stage names
# -----------------------
summary = summary.merge(
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

# -----------------------
# Final columns
# -----------------------
summary = summary[
    [
        "Quarter",
        "pipeline_id",
        "pipeline_name",
        "pipeline_stage_id",
        "stage_name",
        "stage_position",
        "Opportunities",
        "Pipeline_Value",
        "Avg_Age",
    ]
].rename(
    columns={
        "pipeline_stage_id": "stage_id",
    }
)

# Sort chronologically and by stage order
summary["Year"] = summary["Quarter"].str[:4].astype(int)
summary["Q"] = summary["Quarter"].str[-1].astype(int)

summary = (
    summary.sort_values(
        ["Year", "Q", "pipeline_name", "stage_position"]
    )
    .drop(columns=["Year", "Q"])
)

# Save
summary.to_csv(OUTPUT_FILE, index=False)

print(f"Saved {OUTPUT_FILE}")