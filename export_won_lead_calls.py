#!/usr/bin/env python3
"""Export the latest 30 won clients from a GoHighLevel pipeline to CSV.

Required .env values:
  GHL_BEARER_TOKEN, PIPELINE_ID, LOCATION_ID

Optional values:
  None.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
GHL_BASE = "https://services.leadconnectorhq.com"
ALLOWED_OWNER_FIRST_NAMES = {"haitham", "daniel", "christian"}


def load_dotenv(path: Path) -> None:
    """Load simple KEY=value entries without overwriting real environment values."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def api_json(url: str, headers: dict[str, str], *, method: str = "GET", data: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if data is None else json.dumps(data).encode("utf-8")
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed ({error.code}): {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach {url}: {error.reason}") from error


def ghl_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        # Match the working n8n request usezzd for this export.
        "Version": "2021-07-28",
        # GHL's Cloudflare edge rejects urllib's default Python user agent.
        "User-Agent": "ghl-won-client-export/1.0",
    }


def won_opportunities(
    token: str, location_id: str, pipeline_id: str, owners: dict[str, str]
) -> list[dict[str, Any]]:
    headers = ghl_headers(token)
    matched: list[dict[str, Any]] = []
    cursor_start: int | None = None
    cursor_id: str | None = None
    while len(matched) < 30:
        params: dict[str, Any] = {
            "location_id": location_id,
            "pipeline_id": pipeline_id,
            "status": "won",
            "order": "added_desc",
            "limit": 100,
        }
        if cursor_start is None:
            params["page"] = 1
        else:
            params["startAfter"] = cursor_start
            params["startAfterId"] = cursor_id
        result = api_json(
            f"{GHL_BASE}/opportunities/search?{urlencode(params)}", headers
        )
        batch = result.get("opportunities", [])
        for lead in batch:
            owner_name = owners.get(str(lead.get("assignedTo") or ""), "")
            first_name = owner_name.strip().split(maxsplit=1)[0].casefold() if owner_name.strip() else ""
            if first_name in ALLOWED_OWNER_FIRST_NAMES:
                matched.append(lead)
                if len(matched) == 30:
                    return matched
        meta = result.get("meta", {})
        next_start = meta.get("startAfter")
        next_id = meta.get("startAfterId")
        if not batch or next_start is None or not next_id:
            break
        cursor_start, cursor_id = int(next_start), str(next_id)
    return matched


def owner_names(token: str, location_id: str) -> dict[str, str]:
    """Return the GHL display name for each user available in this location."""
    result = api_json(
        f"{GHL_BASE}/users/?{urlencode({'locationId': location_id})}",
        ghl_headers(token),
    )
    return {
        str(user["id"]): str(user.get("name") or user.get("email") or "")
        for user in result.get("users", [])
        if user.get("id")
    }


def get_contact(token: str, contact_id: str) -> dict[str, Any]:
    result = api_json(f"{GHL_BASE}/contacts/{contact_id}", ghl_headers(token))
    return result.get("contact", result)


def build_rows(
    token: str, leads: list[dict[str, Any]], owners: dict[str, str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    contact_cache: dict[str, dict[str, Any]] = {}
    for index, lead in enumerate(leads, start=1):
        contact = lead.get("contact") or {}
        contact_id = str(lead.get("contactId") or contact.get("id") or "")
        if contact_id and not contact.get("email"):
            if contact_id not in contact_cache:
                contact_cache[contact_id] = get_contact(token, contact_id)
            contact = contact_cache[contact_id]

    for index, lead in enumerate(leads, start=1):
        contact = lead.get("contact") or {}
        contact_id = str(lead.get("contactId") or contact.get("id") or "")
        if contact_id and not contact.get("email"):
            contact = contact_cache[contact_id]
        email = str(contact.get("email") or "").strip()
        base = {
            "lead_rank": index,
            "opportunity_id": lead.get("id", ""),
            "lead_name": lead.get("name") or contact.get("name", ""),
            "contact_id": contact_id,
            "contact_email": email,
            "won_at": lead.get("lastStatusChangeAt", ""),
            "opportunity_value": lead.get("monetaryValue", ""),
            "status": lead.get("status", ""),
            "owner_id": lead.get("assignedTo", ""),
            "owner_name": owners.get(str(lead.get("assignedTo") or ""), ""),
        }
        rows.append(base)
    return rows


def main() -> None:
    load_dotenv(ROOT / ".env")
    ghl_token = require_env("GHL_BEARER_TOKEN")
    location_id = require_env("LOCATION_ID")
    pipeline_id = require_env("PIPELINE_ID")
    owners = owner_names(ghl_token, location_id)
    leads = won_opportunities(ghl_token, location_id, pipeline_id, owners)
    print(f"Found {len(leads)} won opportunities for Haitham, Daniel, or Christian; writing client CSV...")
    rows = build_rows(ghl_token, leads, owners)

    output_dir = ROOT / "exports"
    output_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"last_30_won_clients_{stamp}.csv"
    columns = [
        "lead_rank", "opportunity_id", "lead_name", "contact_id", "contact_email", "won_at", "opportunity_value", "status", "owner_id", "owner_name",
    ]
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
