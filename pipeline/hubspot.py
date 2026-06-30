"""
HubSpot client. Pulls all contacts (First/Last/Email/Owner) and the owner
directory (id -> email/name) via the CRM v3 REST API.

Auth: a HubSpot Private App token in env var HUBSPOT_TOKEN, with scopes
  - crm.objects.contacts.read
  - crm.objects.owners.read   (optional but recommended)
"""
import time
import requests

BASE = "https://api.hubapi.com"


class HubSpot:
    def __init__(self, token: str):
        if not token:
            raise RuntimeError("HUBSPOT_TOKEN is empty. Create a Private App token.")
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}"})

    def _get(self, url, params=None):
        for attempt in range(6):
            r = self.s.get(url, params=params, timeout=60)
            if r.status_code == 429:  # rate limited
                time.sleep(2 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        r.raise_for_status()

    def get_owners(self) -> dict:
        """Return {owner_id: {'email':..., 'name':...}}."""
        owners, after = {}, None
        while True:
            params = {"limit": 100}
            if after:
                params["after"] = after
            data = self._get(f"{BASE}/crm/v3/owners", params=params)
            for o in data.get("results", []):
                name = (f"{o.get('firstName','')} {o.get('lastName','')}").strip()
                owners[str(o["id"])] = {"email": (o.get("email") or "").lower(), "name": name}
            after = data.get("paging", {}).get("next", {}).get("after")
            if not after:
                break
        return owners

    def get_contacts(self) -> list:
        """
        Return a list of {first, last, email, owner_id} for every contact.
        Uses the list endpoint with paging (handles 100k+ contacts).
        """
        contacts, after = [], None
        props = "firstname,lastname,email,hubspot_owner_id"
        while True:
            params = {"limit": 100, "properties": props, "archived": "false"}
            if after:
                params["after"] = after
            data = self._get(f"{BASE}/crm/v3/objects/contacts", params=params)
            for c in data.get("results", []):
                p = c.get("properties", {})
                contacts.append({
                    "first": (p.get("firstname") or "").strip(),
                    "last": (p.get("lastname") or "").strip(),
                    "email": (p.get("email") or "").strip().lower(),
                    "owner_id": str(p.get("hubspot_owner_id") or ""),
                })
            after = data.get("paging", {}).get("next", {}).get("after")
            if not after:
                break
        return contacts


def fetch_hubspot(token: str):
    """Return (contacts, owners) where each contact also carries owner_email."""
    hs = HubSpot(token)
    owners = hs.get_owners()
    contacts = hs.get_contacts()
    for c in contacts:
        info = owners.get(c["owner_id"], {})
        c["owner_email"] = info.get("email", "")
        c["owner_name"] = info.get("name", "") or info.get("email", "")
    return contacts, owners
