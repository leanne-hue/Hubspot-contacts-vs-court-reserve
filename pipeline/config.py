"""
Central configuration for the Pickleplex HubSpot x Court Reserve dashboard.

Nothing secret lives here. Credentials are read from environment variables
(which on GitHub come from Actions Secrets). See README.md.
"""
import os

# ---------------------------------------------------------------------------
# Court Reserve locations (the 16 enterprise locations found in the UI).
# Order here is the order shown in the dashboard dropdown.
# ---------------------------------------------------------------------------
COURT_RESERVE_LOCATIONS = [
    "Aurora", "Barrie", "Belleville", "Brantford", "Burloak", "Cambridge",
    "Don Mills", "Downsview", "Oshawa", "Peterborough", "Pickering",
    "Promenade", "Red Deer", "Vaughan", "Windsor", "York Mills",
]

# ---------------------------------------------------------------------------
# Mapping: Court Reserve location name -> HubSpot "Contact Owner" email.
#
# In HubSpot the Contact Owner is a user whose email encodes the location,
# e.g. Vaughan -> vaughan@pickleplex.ca, Don Mills -> donmills@pickleplex.ca.
#
# The default is derived automatically (lowercase, strip spaces, add domain).
# run.py cross-checks these against the REAL owners returned by the HubSpot API
# and warns about any mismatch so you can add an override below.
# ---------------------------------------------------------------------------
OWNER_EMAIL_DOMAIN = "pickleplex.ca"

LOCATION_OWNER_OVERRIDES = {
    # "Promenade": "promenademall@pickleplex.ca",
}


def derive_owner_email(location: str) -> str:
    if location in LOCATION_OWNER_OVERRIDES:
        return LOCATION_OWNER_OVERRIDES[location].lower()
    local = location.lower().replace(" ", "").replace("-", "")
    return f"{local}@{OWNER_EMAIL_DOMAIN}"


def location_owner_map() -> dict:
    return {loc: derive_owner_email(loc) for loc in COURT_RESERVE_LOCATIONS}


# ---------------------------------------------------------------------------
# Secrets / environment
# ---------------------------------------------------------------------------
HUBSPOT_TOKEN = os.environ.get("HUBSPOT_TOKEN", "")
COURT_RESERVE_LOGIN_URL = (os.environ.get("COURT_RESERVE_LOGIN_URL") or
                            "https://app.courtreserve.com/Account/Login")
COURT_RESERVE_USERNAME = os.environ.get("COURT_RESERVE_USERNAME", "")
COURT_RESERVE_PASSWORD = os.environ.get("COURT_RESERVE_PASSWORD", "")

# ---------------------------------------------------------------------------
# Output paths (relative to repo root). GitHub Pages serves the site/ folder.
# ---------------------------------------------------------------------------
SITE_DIR = "docs"   # GitHub Pages serves this folder (branch: main, /docs)
DOWNLOADS_SUBDIR = "downloads"  # site/downloads/<Location>.xlsx

# ---------------------------------------------------------------------------
# PII handling: per-location contact lists are NOT published publicly.
# They are written here and uploaded as a PRIVATE GitHub Actions artifact
# (downloadable only by people logged in with access to the repo).
# ---------------------------------------------------------------------------
OUTREACH_DIR = "outreach_lists"
REPO_URL = "https://github.com/leanne-hue/Hubspot-contacts-vs-court-reserve"
ACTIONS_URL = REPO_URL + "/actions"

# ---------------------------------------------------------------------------
# Court Reserve enterprise org IDs per location (from the Enterprise
# "Organizations" page: /Account/SwitchOrg?id=<orgId> switches context).
# ---------------------------------------------------------------------------
LOCATION_ORGID = {
    "Aurora": 17113, "Barrie": 13487, "Belleville": 15741, "Brantford": 17392,
    "Burloak": 17621, "Cambridge": 16359, "Don Mills": 21849, "Downsview": 15926,
    "Oshawa": 15989, "Peterborough": 17702, "Pickering": 14195, "Promenade": 15917,
    "Red Deer": 16556, "Vaughan": 15790, "Windsor": 13986, "York Mills": 17114,
}
