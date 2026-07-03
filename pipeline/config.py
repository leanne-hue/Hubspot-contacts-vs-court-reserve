"""
Configuration for the Pickleplex HubSpot x Court Reserve dashboard.

HubSpot is pulled live via API. Court Reserve data comes ONLY from manually
uploaded CSV exports in data/court-reserve/ (one CSV per location). No browser
automation. Nothing secret lives here; the HubSpot token is read from env.
"""
import os

# --- Court Reserve CSV data source -----------------------------------------
DATA_DIR = "data/court-reserve"          # one <location>.csv per location

# --- Owner mapping: location name -> HubSpot "Contact Owner" email ----------
# In HubSpot the Contact Owner encodes the location, e.g.
#   Vaughan -> vaughan@pickleplex.ca,  Don Mills -> donmills@pickleplex.ca
OWNER_EMAIL_DOMAIN = "pickleplex.ca"

# Optional overrides if a location's owner email doesn't follow the pattern.
LOCATION_OWNER_OVERRIDES = {
    # "Promenade": "promenademall@pickleplex.ca",
}

# --- List-based locations ----------------------------------------------------
# A location that hasn't opened yet has no real Contact Owner assignments in
# HubSpot, so Contact-Owner-based coverage would be meaningless for it.
# Locations listed here use a HubSpot list/segment (matched by contact ID)
# as their "source" of HubSpot contacts instead of Contact Owner, both for
# the coverage table and for the "not in Court Reserve" download.
# Find a list's ID from its URL in HubSpot: .../objectLists/<ID>/filters
LOCATION_LIST_SOURCE = {
    "Don Mills": 393,   # HubSpot list "Don Mills" -- pre-opening mailing list
}


def derive_owner_email(location: str) -> str:
    """'Don Mills' -> donmills@pickleplex.ca ; 'Vaughan' -> vaughan@pickleplex.ca"""
    if location in LOCATION_OWNER_OVERRIDES:
        return LOCATION_OWNER_OVERRIDES[location].lower()
    local = location.lower().replace(" ", "").replace("-", "").replace("_", "")
    return f"{local}@{OWNER_EMAIL_DOMAIN}"


# --- Secrets / environment --------------------------------------------------
HUBSPOT_TOKEN = os.environ.get("HUBSPOT_TOKEN", "")

# --- Output paths (GitHub Pages serves docs/) -------------------------------
SITE_DIR = "docs"
DOWNLOADS_SUBDIR = "downloads"
OUTREACH_DIR = "outreach_lists"          # unused (kept for backward compat)
REPO_URL = "https://github.com/leanne-hue/Hubspot-contacts-vs-court-reserve"
ACTIONS_URL = REPO_URL + "/actions"
