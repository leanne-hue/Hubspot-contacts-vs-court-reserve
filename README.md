# Pickleplex — HubSpot × Court Reserve Coverage Dashboard

Groups HubSpot contacts by **Contact Owner** (your location dimension) and
cross-references each Court Reserve location's members (matched by **email**) to
show coverage and produce per-location "not yet a member" outreach lists.

Published via **GitHub Pages**, refreshed **every Monday at 10:00 AM
America/Toronto** (and immediately whenever you update a Court Reserve CSV).

**Live dashboard:** https://leanne-hue.github.io/Hubspot-contacts-vs-court-reserve/

---

## Data sources

- **HubSpot** — pulled automatically via the HubSpot API (Private App token in
  the `HUBSPOT_TOKEN` Actions secret). ~123K contacts, owner = location.
- **Court Reserve** — read from **CSV files you upload** to
  `data/court-reserve/`. No scraping/automation (Court Reserve has bot
  protection). One CSV per location; the filename is the location name.

---

## 🔄 How to update Court Reserve data (do this whenever you want fresh numbers)

For **each** Court Reserve location:

1. Log into Court Reserve and switch to that location.
2. Go to **Reports → Members**.
3. Set the filters to include **all** members (clear any status/date filters;
   include active + inactive), then **export as CSV**.
4. Rename the file to the location name and put it in **`data/court-reserve/`**,
   replacing the existing file. Examples:
   - Don Mills → `data/court-reserve/don-mills.csv`
   - York Mills → `data/court-reserve/york-mills.csv`
   - Vaughan → `data/court-reserve/vaughan.csv`
5. **Commit and push.** The GitHub Action rebuilds the dashboard automatically
   (usually live within ~2 minutes).

Notes:
- The pipeline **auto-detects** whatever CSVs are in the folder — add a new
  location just by adding a CSV; remove one by deleting its CSV.
- Filenames become location names: hyphens/underscores become spaces and each
  word is capitalized (`red-deer.csv` → "Red Deer").
- The dashboard shows **"Court Reserve data uploaded: <date>"** based on the
  last commit that changed this folder, so everyone knows how fresh it is.
- Only the **Email** column is used (lowercased + trimmed). Other columns are
  ignored, so extra columns in your export are fine.

Expected CSV columns (from Court Reserve's Members report export) include:
`Member #, First Name, Last Name, Gender, Family, Family Role, Email,
Current Membership, Membership Status, ...` — the pipeline finds the **Email**
column by name (comma- or tab-separated both work).

---

## Repository layoutdata/court-reserve/         <-- drop one <location>.csv here per location

pipeline/

config.py                 owner-email mapping, paths

hubspot.py                HubSpot API pull (unchanged)

courtreserve.py           reads the CSVs in data/court-reserve/

render.py                 builds dataset, Excel files, dashboard HTML

dashboard_template.py     the self-contained dashboard

run.py                    orchestrator (what the weekly job runs)

make_demo.py              synthetic preview (no network)

.github/workflows/update_dashboard.yml

docs/                       GitHub Pages output (index.html)

requirements.txt## What's on the dashboard

- Location dropdown (all locations that have a CSV).
- Coverage table: for the selected location's members, how many of each Contact
  Owner's HubSpot contacts are already Court Reserve members, with % coverage.
- Contacts-by-Contact-Owner table: the full HubSpot base (all owners).
- Download button → the private **outreach-lists** artifact on the Actions page
  (GitHub login required): every HubSpot contact under that location's owner who
  is NOT yet in Court Reserve (First Name, Last Name, Email, Contact Owner).
  Contact-level PII is kept off the public page.

## Run locally (optional)
```bash
pip install -r requirements.txt
export HUBSPOT_TOKEN=pat-na...
python pipeline/run.py          # reads data/court-reserve/*.csv, writes docs/
python pipeline/make_demo.py    # synthetic preview, no token needed
```
