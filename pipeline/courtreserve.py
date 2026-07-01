"""
Court Reserve client (Playwright).

This is an ENTERPRISE account: after login you land on the Enterprise
Organizations page, and each location is switched by URL:
    /Account/SwitchOrg?id=<orgId>
After switching, /Member/Index?filter=all shows that location's members and the
"Export" button (button.btn-print-excel) downloads the full member spreadsheet.

Flow:
  1. Log in (robust, selector-agnostic: fill the password field + the first
     visible text/email field, submit).
  2. For each location: SwitchOrg -> open member list -> Export -> read emails.

A screenshot is saved to /tmp/cr_debug on any failure. Never writes under docs/.
"""
import os
import re
import time
import csv
import openpyxl
from playwright.sync_api import sync_playwright

from config import (
    COURT_RESERVE_LOGIN_URL, COURT_RESERVE_USERNAME, COURT_RESERVE_PASSWORD,
    COURT_RESERVE_LOCATIONS, LOCATION_ORGID,
)

BASE = "https://app.courtreserve.com"
MEMBER_LIST_URL = BASE + "/Member/Index?filter=all"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
DEBUG_DIR = "/tmp/cr_debug"


def _dump(page, name):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    try:
        page.screenshot(path=f"{DEBUG_DIR}/{name}.png", full_page=True)
    except Exception:
        pass


def _login(page):
    page.goto(COURT_RESERVE_LOGIN_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    # Password field is unambiguous; the username is the first visible text/email input.
    page.wait_for_selector("input[type=password]", timeout=45000)
    page.locator("input[type=email], input[type=text]").first.fill(COURT_RESERVE_USERNAME)
    page.locator("input[type=password]").first.fill(COURT_RESERVE_PASSWORD)
    page.locator("button[type=submit], input[type=submit], button:has-text('Sign In'), "
                 "button:has-text('Log In')").first.click()
    page.wait_for_load_state("networkidle")
    if "/Account/Login" in page.url:
        _dump(page, "login_failed")
        raise RuntimeError("Court Reserve login failed (still on /Account/Login). "
                           "Check COURT_RESERVE_USERNAME / COURT_RESERVE_PASSWORD or 2FA.")


def _emails_from_spreadsheet(path):
    emails = set()
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.reader(f):
                for v in row:
                    v = (v or "").strip().lower()
                    if EMAIL_RE.fullmatch(v):
                        emails.add(v)
        return emails
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            for v in row:
                if v:
                    s = str(v).strip().lower()
                    if EMAIL_RE.fullmatch(s):
                        emails.add(s)
    return emails


def _export_org_emails(page, org_id):
    page.goto(f"{BASE}/Account/SwitchOrg?id={org_id}", wait_until="domcontentloaded")
    page.goto(MEMBER_LIST_URL, wait_until="networkidle")
    page.wait_for_timeout(1500)
    with page.expect_download(timeout=180000) as dl_info:
        page.click("button.btn-print-excel, button:has-text('Export'), a:has-text('Export')")
    dl = dl_info.value
    target = os.path.join("/tmp", dl.suggested_filename or f"members_{org_id}.xlsx")
    dl.save_as(target)
    return _emails_from_spreadsheet(target)


def fetch_court_reserve(locations=None, headless=True) -> dict:
    """Return {location_name: set(member_emails)} for every location."""
    locations = locations or COURT_RESERVE_LOCATIONS
    result = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.set_default_timeout(60000)

        _login(page)

        for loc in locations:
            org_id = LOCATION_ORGID.get(loc)
            if not org_id:
                print(f"  [warn] no orgId configured for {loc}; skipping")
                result[loc] = set()
                continue
            try:
                emails = _export_org_emails(page, org_id)
            except Exception as e:
                _dump(page, f"loc_{loc.replace(' ', '_')}")
                print(f"  [warn] export failed for {loc} (org {org_id}): {e}")
                emails = set()
            result[loc] = emails
            print(f"  {loc} (org {org_id}): {len(emails)} member emails")
            time.sleep(1)

        browser.close()
    return result
