# Pickleplex — HubSpot × Court Reserve Coverage Dashboard

A self-contained dashboard that groups HubSpot contacts by **Contact Owner**
(your location dimension) and cross-references each Court Reserve location's
member list (matched by **email**) to show coverage and produce per-location
"not yet a member" outreach lists for marketing.

Published via **GitHub Pages**, refreshed automatically **every Monday at
10:00 AM America/Toronto** by a GitHub Actions workflow.

---

## What it shows

- **Location dropdown** (all 16 Court Reserve locations) at the top. Everything
  below updates when you switch locations.
- **Court Reserve Coverage table** — for the selected location's members, how
  many of each Contact Owner's HubSpot contacts already exist in Court Reserve,
  with a `% Coverage` column. The owner that maps to the selected location is
  highlighted.
- **Contacts by Contact Owner table** — the **full HubSpot picture** across all
  owners, shown regardless of the dropdown (design choice: this is the most
  useful constant reference; it's noted on the dashboard).
- **Download button** — a per-location Excel file (`Download — <Location>`) of
  every HubSpot contact under that location's owner who is **not** in that
  location's Court Reserve member list. Sheet: `Not in Court Reserve`,
  columns: First Name, Last Name, Email, Contact Owner.

---

## Repository layout

```
pipeline/
  config.py              locations, owner-email mapping, env/secrets
  hubspot.py             pulls all contacts + owners via the HubSpot API
  courtreserve.py        Playwright: logs in, exports members per location
  render.py              builds the dataset, writes Excel files, renders HTML
  dashboard_template.py  the self-contained dashboard HTML
  run.py                 orchestrator (this is what the weekly job runs)
  make_demo.py           generates a synthetic PREVIEW (no network/secrets)
.github/workflows/update_dashboard.yml   weekly cron
docs/                    GitHub Pages output (index.html + downloads/*.xlsx)
requirements.txt
```

---

## One-time setup

### 1. Create the HubSpot Private App token
HubSpot → **Settings → Integrations → Private Apps → Create a private app**.
On the **Scopes** tab enable:
- `crm.objects.contacts.read`
- `crm.objects.owners.read`

Create it and copy the token (starts with `pat-na...`).

### 2. Add GitHub Actions Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**.
Create these **exact** names:

| Secret name | Value |
|---|---|
| `HUBSPOT_TOKEN` | the HubSpot private-app token |
| `COURT_RESERVE_USERNAME` | your Court Reserve login email |
| `COURT_RESERVE_PASSWORD` | your Court Reserve password |
| `COURT_RESERVE_LOGIN_URL` | `https://app.courtreserve.com/Account/Login` (only if the login page differs) |

### 3. Enable GitHub Pages
Repo → **Settings → Pages** → Build and deployment → **Deploy from a branch** →
Branch: **main**, folder: **/docs** → Save. Your URL will be
`https://leanne-hue.github.io/Hubspot-contacts-vs-court-reserve/`.

### 4. First run
Repo → **Actions → Update dashboard → Run workflow** (manual trigger). When it
finishes, the `docs/` folder is populated and Pages serves the dashboard.

---

## How the weekly schedule works
GitHub cron is **UTC only and ignores Daylight Saving**. The workflow therefore
fires at both `14:00 UTC` and `15:00 UTC` every Monday, and a guard step exits
unless it is genuinely 10:00 in `America/Toronto`. Result: it runs once, at
10:00 AM Toronto time, all year round.

---

## ⚠️ Important: Court Reserve on a cloud runner
Court Reserve has no public API for this account, so the pipeline logs into the
website with Playwright and uses the member **Export**. You confirmed login is
**username + password only** (no 2FA), which is what makes unattended automation
possible. Two things to watch on the first scheduled run:

1. **Bot/IP checks.** Court Reserve may challenge logins from datacenter IPs
   (GitHub's runners). If the job's log shows a login failure, the fix is a
   **self-hosted runner** on a Pickleplex machine (Settings → Actions → Runners
   → New self-hosted runner). The same workflow then runs from your own IP where
   you already log in normally. No code changes needed — just change
   `runs-on: ubuntu-latest` to `runs-on: self-hosted`.
2. **Selector drift.** If Court Reserve changes its UI, the export step saves a
   screenshot to `docs/_debug/` so you can see what happened and adjust the
   selector in `courtreserve.py`.

---

## Run locally (optional)
```bash
pip install -r requirements.txt
python -m playwright install chromium
export HUBSPOT_TOKEN=pat-na...
export COURT_RESERVE_USERNAME=you@pickleplex.ca
export COURT_RESERVE_PASSWORD=********
python pipeline/run.py          # writes docs/
```
Preview the layout with synthetic data (no secrets needed):
```bash
python pipeline/make_demo.py    # writes docs/ with fake numbers
```

---

## Owner ↔ location mapping
`pipeline/config.py` derives each owner email from the location name
(`Vaughan → vaughan@pickleplex.ca`, `Don Mills → donmills@pickleplex.ca`). On
each run, `run.py` checks these against the real HubSpot owners and prints a
warning for any mismatch; add an override in `LOCATION_OWNER_OVERRIDES` if one
location's owner email doesn't follow the pattern.
