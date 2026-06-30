"""
Orchestrator: pull HubSpot + Court Reserve, build the dashboard and Excel files.
Run from the repo root:  python pipeline/run.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import config
from hubspot import fetch_hubspot
from courtreserve import fetch_court_reserve
from render import build_dataset, write_excels, render_html


def main():
    print("1/4  Pulling HubSpot contacts + owners ...")
    contacts, owners = fetch_hubspot(config.HUBSPOT_TOKEN)
    print(f"     {len(contacts):,} contacts, {len(owners)} owners")

    # Validate the location -> owner-email mapping against real owners.
    real_emails = {o["email"] for o in owners.values() if o["email"]}
    for loc, email in config.location_owner_map().items():
        if email not in real_emails:
            print(f"     [warn] derived owner '{email}' for location '{loc}' "
                  f"was not found among HubSpot owners. Add an override in config.py.")

    print("2/4  Pulling Court Reserve members for all locations ...")
    cr = fetch_court_reserve(headless=True)

    print("3/4  Building dataset + Excel outreach lists ...")
    data, not_in_cr = build_dataset(contacts, cr)
    os.makedirs(config.SITE_DIR, exist_ok=True)
    write_excels(not_in_cr)  # -> private outreach_lists/

    print("4/4  Rendering dashboard HTML ...")
    with open(os.path.join(config.SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_html(data))

    # .nojekyll so GitHub Pages serves files/folders starting with _ etc.
    open(os.path.join(config.SITE_DIR, ".nojekyll"), "w").close()
    print("Done. Output in", config.SITE_DIR)


if __name__ == "__main__":
    main()
