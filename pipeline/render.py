"""
Builds the dashboard dataset from HubSpot contacts + Court Reserve member sets,
writes one Excel file per location ("Not in Court Reserve" outreach lists) into
a PRIVATE folder (uploaded as a GitHub Actions artifact, never published), and
renders the self-contained public dashboard HTML (aggregate data only, no PII).
"""
import os
import json
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

import openpyxl
from openpyxl.styles import Font, PatternFill

from config import (
    COURT_RESERVE_LOCATIONS, location_owner_map, OUTREACH_DIR, ACTIONS_URL,
)

TZ = ZoneInfo("America/Toronto")


def build_dataset(contacts, cr_members_by_location):
    """
    contacts: list of {first,last,email,owner_email,owner_name}
    cr_members_by_location: {location: set(emails)}
    Returns (data_dict_for_dashboard, not_in_cr_rows).
    The embedded data contains ONLY aggregate counts -- no contact names/emails.
    """
    owner_map = location_owner_map()

    by_owner = defaultdict(list)
    for c in contacts:
        by_owner[c["owner_email"]].append(c)

    owner_name_for = {}
    for c in contacts:
        if c["owner_email"] and c["owner_email"] not in owner_name_for:
            owner_name_for[c["owner_email"]] = c.get("owner_name") or c["owner_email"]

    contacts_by_owner = []
    for email, lst in by_owner.items():
        contacts_by_owner.append({
            "owner_name": owner_name_for.get(email, email or "(Unassigned)"),
            "owner_email": email or "",
            "count": len(lst),
        })
    contacts_by_owner.sort(key=lambda r: r["count"], reverse=True)
    total_contacts = len(contacts)

    owners_in_order = [r["owner_email"] for r in contacts_by_owner]
    by_location = {}
    not_in_cr_rows = {}

    for loc in COURT_RESERVE_LOCATIONS:
        cr_emails = cr_members_by_location.get(loc, set())
        coverage = []
        for owner_email in owners_in_order:
            own_contacts = by_owner.get(owner_email, [])
            in_cr = sum(1 for c in own_contacts if c["email"] and c["email"] in cr_emails)
            n = len(own_contacts)
            pct = round(100.0 * in_cr / n, 1) if n else 0.0
            coverage.append({
                "owner_name": owner_name_for.get(owner_email, owner_email or "(Unassigned)"),
                "owner_email": owner_email or "",
                "hubspot_contacts": n,
                "in_cr": in_cr,
                "pct": pct,
            })

        mapped_owner = owner_map[loc]
        mapped_contacts = by_owner.get(mapped_owner, [])
        missing = [c for c in mapped_contacts if not c["email"] or c["email"] not in cr_emails]
        not_in_cr_rows[loc] = missing

        by_location[loc] = {
            "owner_email": mapped_owner,
            "owner_name": owner_name_for.get(mapped_owner, mapped_owner),
            "cr_member_count": len(cr_emails),
            "coverage": coverage,
            "not_in_cr_count": len(missing),
        }

    data = {
        "generated_at": datetime.now(TZ).strftime("%A, %B %-d, %Y at %-I:%M %p %Z"),
        "locations": COURT_RESERVE_LOCATIONS,
        "owner_map": owner_map,
        "total_contacts": total_contacts,
        "contacts_by_owner": contacts_by_owner,
        "by_location": by_location,
        "artifacts_url": ACTIONS_URL,
    }
    return data, not_in_cr_rows


def _safe(name):
    return name.replace(" ", "_").replace("/", "-")


def write_excels(not_in_cr_rows, out_dir=OUTREACH_DIR):
    """Write one xlsx per location into the PRIVATE outreach folder."""
    os.makedirs(out_dir, exist_ok=True)
    owner_map = location_owner_map()
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F6F43")
    for loc, rows in not_in_cr_rows.items():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Not in Court Reserve"
        ws.append(["First Name", "Last Name", "Email", "Contact Owner"])
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
        for c in rows:
            ws.append([c.get("first", ""), c.get("last", ""), c.get("email", ""),
                       c.get("owner_email", owner_map[loc])])
        for col, width in zip("ABCD", (20, 20, 34, 28)):
            ws.column_dimensions[col].width = width
        ws.freeze_panes = "A2"
        wb.save(os.path.join(out_dir, f"{_safe(loc)}.xlsx"))


def render_html(data) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return HTML_TEMPLATE.replace("/*__DATA__*/", payload)


from dashboard_template import HTML_TEMPLATE  # noqa: E402
