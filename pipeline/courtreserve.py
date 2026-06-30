"""
Court Reserve client (browser automation via Playwright).

Court Reserve has no public API for this account, and the member grid refuses
to display the full list (>500 members) -- it points you at the Export. So we
drive the authenticated UI:

  1. Log in once with username + password.
  2. For each of the 16 locations: switch the org (the green dropdown top-left),
     open the Member list, click "Export", capture the downloaded spreadsheet,
     and read every member's email.

As a safety net we also intercept the backend members API
(backend.courtreserve.com/api/member-management/members) and harvest any emails
that appear in those JSON responses while the page is open.

If a selector ever drifts (Court Reserve ships UI changes), the functions raise
with a screenshot saved to site/_debug so you can see what the page looked like.
"""
import os
import re
import time
import glob
import openpyxl
from playwright.sync_api import sync_playwright

from config import (
    COURT_RESERVE_LOGIN_URL,
    COURT_RESERVE_USERNAME,
    COURT_RESERVE_PASSWORD,
    COURT_RESERVE_LOCATIONS,
)

MEMBER_LIST_URL = "https://app.courtreserve.com/Member/Index?filter=all"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
DEBUG_DIR = "docs/_debug"


def _dump(page, name):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    try:
        page.screenshot(path=f"{DEBUG_DIR}/{name}.png", full_page=True)
    except Exception:
        pass


def _login(page):
    page.goto(COURT_RESERVE_LOGIN_URL, wait_until="domcontentloaded")
    # Court Reserve login form: username + password fields, then a submit button.
    page.fill("input[name='UserNameOrEmail'], input[name='Username'], input#UserNameOrEmail, input[type='email']", COURT_RESERVE_USERNAME)
    page.fill("input[name='Password'], input#Password, input[type='password']", COURT_RESERVE_PASSWORD)
    page.click("button[type='submit'], input[type='submit'], button:has-text('Sign In'), button:has-text('Log In')")
    page.wait_for_load_state("networkidle")
    if "Login" in page.url:
        _dump(page, "login_failed")
        raise RuntimeError("Court Reserve login appears to have failed (still on Login page). "
                           "Check COURT_RESERVE_USERNAME / COURT_RESERVE_PASSWORD, or 2FA may be enabled.")


def _switch_location(page, location: str):
    """Open the green org dropdown (top-left) and click the location by name."""
    # The dropdown toggle is the coloured org box at the very top-left.
    page.click(".organization-switcher, .navbar-brand, [class*='org']:has-text('')", timeout=5000) if False else None
    # Robust path: click the element showing the current org name, then the option.
    try:
        page.get_by_role("button").filter(has_text=re.compile("|".join(COURT_RESERVE_LOCATIONS))).first.click(timeout=4000)
    except Exception:
        # Fallback: click top-left header area
        page.mouse.click(70, 60)
    page.wait_for_timeout(500)
    page.get_by_text(location, exact=True).first.click(timeout=8000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)


def _export_members(page) -> str:
    """Click Export on the member list and return the downloaded file path."""
    page.goto(MEMBER_LIST_URL, wait_until="networkidle")
    page.wait_for_timeout(1500)
    with page.expect_download(timeout=120000) as dl_info:
        page.click("button:has-text('Export'), a:has-text('Export'), .k-button:has-text('Export')")
    download = dl_info.value
    target = os.path.join("/tmp", download.suggested_filename)
    download.save_as(target)
    return target


def _emails_from_spreadsheet(path: str):
    """Read an exported .xlsx/.csv and return (rows, emails) where rows are dicts."""
    rows, emails = [], set()
    if path.lower().endswith(".csv"):
        import csv
        with open(path, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                _collect_row(r, rows, emails)
        return rows, emails
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    headers = None
    for row in ws.iter_rows(values_only=True):
        if headers is None:
            headers = [str(h).strip().lower() if h is not None else "" for h in row]
            continue
        rec = {headers[i]: row[i] for i in range(len(headers)) if i < len(row)}
        _collect_row(rec, rows, emails)
    return rows, emails


def _collect_row(rec, rows, emails):
    # find an email-ish value in the row
    email = ""
    for k, v in rec.items():
        if v and "email" in str(k).lower():
            email = str(v).strip().lower()
            break
    if not email:
        for v in rec.values():
            if v and EMAIL_RE.fullmatch(str(v).strip()):
                email = str(v).strip().lower()
                break
    if email and EMAIL_RE.fullmatch(email):
        emails.add(email)
        rows.append(rec)


def fetch_court_reserve(locations=None, headless=True) -> dict:
    """
    Return {location_name: set_of_member_emails} for every location.
    """
    locations = locations or COURT_RESERVE_LOCATIONS
    result = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

        # Harvest emails from any backend member API responses, as a safety net.
        api_emails = {"current": set()}

        def on_response(resp):
            if "member-management/members" in resp.url:
                try:
                    txt = resp.text()
                    for m in EMAIL_RE.findall(txt):
                        api_emails["current"].add(m.lower())
                except Exception:
                    pass

        page.on("response", on_response)

        _login(page)

        for loc in locations:
            api_emails["current"] = set()
            try:
                _switch_location(page, loc)
                path = _export_members(page)
                _, emails = _emails_from_spreadsheet(path)
            except Exception as e:
                _dump(page, f"location_{loc.replace(' ', '_')}_error")
                print(f"  [warn] Export failed for {loc}: {e}. Falling back to API-intercept emails.")
                emails = set()
            emails |= api_emails["current"]  # union with anything the API leaked
            result[loc] = emails
            print(f"  {loc}: {len(emails)} member emails")
            time.sleep(1)

        browser.close()
    return result
