"""
Builds the dashboard dataset from HubSpot contacts + Court Reserve member sets
(read from CSVs), writes one private xlsx per location ("Not in Court Reserve"),
and renders the self-contained public dashboard HTML (aggregate data only).

Locations are inferred from whatever Court Reserve CSVs exist -- not hardcoded.
"""
import os
import json
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

import openpyxl
from openpyxl.styles import Font, PatternFill

from config import derive_owner_email, OUTREACH_DIR, ACTIONS_URL

TZ = ZoneInfo("America/Toronto")


def build_dataset(contacts, cr_members_by_location, cr_last_uploaded="unknown"):
    """
    contacts: list of {first,last,email,owner_email,owner_name}
    cr_members_by_location: {location: set(emails)}  (locations inferred from CSVs)
    Returns (data_for_dashboard, not_in_cr_rows). Embedded data = aggregate only.
    """
    locations = sorted(cr_members_by_location.keys())
    owner_map = {loc: derive_owner_email(loc) for loc in locations}

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

    for loc in locations:
        cr_emails = cr_members_by_location.get(loc, set())
        coverage = []
        for owner_email in owners_in_order:
            own = by_owner.get(owner_email, [])
            in_cr = sum(1 for c in own if c["email"] and c["email"] in cr_emails)
            n = len(own)
            coverage.append({
                "owner_name": owner_name_for.get(owner_email, owner_email or "(Unassigned)"),
                "owner_email": owner_email or "",
                "hubspot_contacts": n,
                "in_cr": in_cr,
                "pct": round(100.0 * in_cr / n, 1) if n else 0.0,
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
        "cr_last_uploaded": cr_last_uploaded,
        "locations": locations,
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
    os.makedirs(out_dir, exist_ok=True)
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
                       c.get("owner_email", derive_owner_email(loc))])
        for col, width in zip("ABCD", (20, 20, 34, 28)):
            ws.column_dimensions[col].width = width
        ws.freeze_panes = "A2"
        wb.save(os.path.join(out_dir, f"{_safe(loc)}.xlsx"))


def render_html(data) -> str:
    return HTML_TEMPLATE.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))


from dashboard_template import HTML_TEMPLATE  # noqa: E402
