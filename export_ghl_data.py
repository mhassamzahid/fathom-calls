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

def export_contacts():

    contacts = []
    start_after = None

    while True:

        params = {
            "locationId": LOCATION_ID,
            "limit": 100
        }

        if start_after:
            params["startAfter"] = start_after

        r = requests.get(
            f"{BASE}/contacts/",
            headers=HEADERS_CONTACTS,
            params=params
        )

        r.raise_for_status()

        data = r.json()

        batch = data.get("contacts", [])

        if not batch:
            break

        print(f"Fetched {len(batch)} contacts")

        for c in batch:

            attributions = c.get("attributions", [])

            row = {
                "contact_id": c.get("id"),
                "contact_name": c.get("contactName"),
                "email": c.get("email"),
                "phone": c.get("phone"),
                "source": c.get("source"),
                "created_at": c.get("dateAdded"),
                "updated_at": c.get("dateUpdated"),
                "assigned_to": c.get("assignedTo"),
                "tags": ",".join(c.get("tags", []))
            }

            # Merge attribution values
            row["utm_source"] = ",".join(
                sorted(set(a.get("source", "") for a in attributions if a.get("source")))
            )

            row["utm_medium"] = ",".join(
                sorted(set(a.get("medium", "") for a in attributions if a.get("medium")))
            )

            row["utm_campaign"] = ",".join(
                sorted(set(a.get("campaign", "") for a in attributions if a.get("campaign")))
            )

            row["utm_session_source"] = ",".join(
                sorted(set(a.get("utmSessionSource", "") for a in attributions if a.get("utmSessionSource")))
            )

            contacts.append(row)

        start_after = batch[-1]["startAfter"]

    df = pd.DataFrame(contacts)
    df.to_csv("contacts.csv", index=False)

    print(f"Saved {len(df)} contacts")
    
def export_opportunities():

    opportunities = []

    page = 0

    while True:

        body = {
            "locationId": LOCATION_ID,
            "limit": 500,
            "page": page,
            "filters": [
                {
                    "field": "pipeline_id",
                    "operator": "eq",
                    "value": PIPELINE_ID
                }
            ]
        }

        r = requests.post(
            f"{BASE}/opportunities/search",
            headers=HEADERS_V3,
            json=body
        )

        r.raise_for_status()

        data = r.json()

        batch = data.get("opportunities", [])

        if not batch:
            break

        print(f"Fetched page {page}: {len(batch)} opportunities")

        for o in batch:

            attributions = o.get("attributions", [])

            row = {
                "opportunity_id": o.get("id"),
                "contact_id": o.get("contactId"),
                "contact_name": o.get("name"),
                "pipeline_id": o.get("pipelineId"),
                "pipeline_stage_id": o.get("pipelineStageId"),
                "assigned_to": o.get("assignedTo"),
                "status": o.get("status"),
                "monetary_value": o.get("monetaryValue"),
                "source": o.get("source"),
                "contact_email": o.get("contact").get("email") if o.get("contact") else None,
                "created_at": o.get("createdAt"),
                "updated_at": o.get("updatedAt"),
                "last_stage_change_at": o.get("lastStageChangeAt"),
                "last_status_change_at": o.get("lastStatusChangeAt")
            }

            row["utm_source"] = ",".join(
                sorted(set(a.get("source", "") for a in attributions if a.get("source")))
            )

            row["utm_medium"] = ",".join(
                sorted(set(a.get("medium", "") for a in attributions if a.get("medium")))
            )

            row["utm_campaign"] = ",".join(
                sorted(set(a.get("campaign", "") for a in attributions if a.get("campaign")))
            )

            row["utm_session_source"] = ",".join(
                sorted(set(a.get("utmSessionSource", "") for a in attributions if a.get("utmSessionSource")))
            )

            opportunities.append(row)

        page += 1

    df = pd.DataFrame(opportunities)
    df.to_csv("opportunities.csv", index=False)

    print(f"Saved {len(df)} opportunities")
    
if __name__ == "__main__":

    export_contacts()
    export_opportunities()

    print("Done.")