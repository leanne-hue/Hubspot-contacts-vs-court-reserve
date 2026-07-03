"""
Orchestrator: pull HubSpot via API, read Court Reserve CSVs, build dashboard + Excel.
Run from the repo root:  python pipeline/run.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import config
from hubspot import fetch_hubspot
from courtreserve import fetch_court_reserve, last_uploaded_display
from render import build_dataset, write_excels, render_html


def main():
    print("1/4  Pulling HubSpot contacts + owners ...")
    contacts, owners = fetch_hubspot(config.HUBSPOT_TOKEN)
    print(f"     {len(contacts):,} contacts, {len(owners)} owners")

    print("2/4  Reading Court Reserve CSVs from", config.DATA_DIR, "...")
    cr = fetch_court_reserve()
    if not cr:
        print("     [warn] no CSVs found in data/court-reserve/ — coverage will be empty.")
    for loc in sorted(cr):
        print(f"     {loc}: {len(cr[loc]):,} member emails")
    last_uploaded = last_uploaded_display()

    print("3/4  Building dataset + Excel outreach lists ...")
    data, not_in_cr = build_dataset(contacts, cr, last_uploaded)
    os.makedirs(config.SITE_DIR, exist_ok=True)
    write_excels(not_in_cr)

    print("4/4  Rendering dashboard HTML ...")
    with open(os.path.join(config.SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_html(data))
    open(os.path.join(config.SITE_DIR, ".nojekyll"), "w").close()
    print("Done. Output in", config.SITE_DIR)


if __name__ == "__main__":
    main()
