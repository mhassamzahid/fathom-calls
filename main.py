import pandas as pd
import numpy as np

# -----------------------------
# Load data
# -----------------------------

contacts = pd.read_csv("contacts.csv", low_memory=False)
opps = pd.read_csv("opportunities.csv", low_memory=False)

# -----------------------------
# Dates
# -----------------------------

contacts["created_at"] = pd.to_datetime(
    contacts["created_at"],
    utc=True,
    errors="coerce"
)

contacts["month"] = contacts["created_at"].dt.to_period("M").astype(str)

# -----------------------------
# Remove obvious junk
# -----------------------------

contacts["email"] = contacts["email"].fillna("").str.lower()
contacts["contact_name"] = contacts["contact_name"].fillna("")
contacts["tags"] = contacts["tags"].fillna("").str.lower()

contacts = contacts[
    ~contacts["email"].str.contains(
        r"test|example\.com|fake|demo",
        regex=True,
        na=False
    )
]

contacts = contacts[
    ~contacts["contact_name"].str.contains(
        r"test|dummy|asdf",
        case=False,
        regex=True,
        na=False
    )
]

# Remove duplicate contacts
contacts = contacts.drop_duplicates(subset="contact_id")

# -----------------------------
# Booked Call?
# -----------------------------

booked = set(opps["contact_id"].dropna().unique())

contacts["booked_call"] = contacts["contact_id"].isin(booked)

# -----------------------------
# Normalise Acquisition Source
# -----------------------------

def acquisition_source(row):

    values = [
        row.get("utm_source"),
        row.get("source"),
        row.get("utm_session_source"),
        row.get("utm_medium"),
        row.get("referrers"),
        row.get("page_urls"),
    ]

    values = [
        str(v).strip()
        for v in values
        if pd.notna(v) and str(v).strip() != ""
    ]

    text = " ".join(values).lower()

    if "webinar" in text:
        return "Webinar"

    if "linkedin" in text:
        return "LinkedIn"

    if "facebook" in text or "meta" in text:
        return "Facebook"

    if "instagram" in text:
        return "Instagram"

    if "google" in text:
        return "Google"

    if "email" in text:
        return "Email"

    if "referral" in text:
        return "Referral"

    if "partner" in text:
        return "Partner"

    if "direct" in text:
        return "Direct"

    if "survey" in text:
        return "Survey"

    if "zapier" in text:
        return "Zapier"

    return "Unknown"


contacts["acquisition_source"] = contacts.apply(
    acquisition_source,
    axis=1
)

# -----------------------------
# Monthly Conversion
# -----------------------------

summary = (
    contacts
    .groupby(["month", "acquisition_source"])
    .agg(
        leads=("contact_id", "count"),
        clarity_calls=("booked_call", "sum")
    )
    .reset_index()
)

summary["conversion_rate"] = (
    summary["clarity_calls"]
    / summary["leads"]
    * 100
).round(2)

summary = summary.sort_values(
    ["month", "conversion_rate"],
    ascending=[True, False]
)

# -----------------------------
# Overall
# -----------------------------

overall = (
    contacts
    .groupby("acquisition_source")
    .agg(
        leads=("contact_id", "count"),
        clarity_calls=("booked_call", "sum")
    )
    .reset_index()
)

overall["conversion_rate"] = (
    overall["clarity_calls"]
    / overall["leads"]
    * 100
).round(2)

overall = overall.sort_values(
    "conversion_rate",
    ascending=False
)

# -----------------------------
# Save
# -----------------------------

summary.to_csv(
    "monthly_source_conversion.csv",
    index=False
)

overall.to_csv(
    "overall_source_conversion.csv",
    index=False
)

contacts.to_csv(
    "contacts_with_conversion.csv",
    index=False
)

print("\nDone.\n")

print(summary.head(20))

print("\nOverall\n")

print(overall)