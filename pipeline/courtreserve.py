"""
Court Reserve data source = manually uploaded CSV exports (NO browser automation).

Each CSV in data/court-reserve/ is one location; the filename (without .csv) is
the location name, inferred at runtime (nothing hardcoded). Emails are read from
the "Email" column (case-insensitive), lowercased and trimmed.

Export instructions for updating the CSVs are in the repo README.
"""
import os
import re
import csv
import glob
import subprocess
from datetime import datetime, timezone

from config import DATA_DIR

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def canonical_location(path: str) -> str:
    """data/court-reserve/don-mills.csv -> 'Don Mills'."""
    base = os.path.splitext(os.path.basename(path))[0]
    words = re.sub(r"[-_]+", " ", base).strip().split()
    return " ".join(w.capitalize() for w in words)


def _emails_from_csv(path: str) -> set:
    emails = set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(8192)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        except Exception:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        headers = reader.fieldnames or []
        # locate the email column (exact 'email' first, then any header containing it)
        email_col = next((h for h in headers if h and h.strip().lower() == "email"), None)
        if not email_col:
            email_col = next((h for h in headers if h and "email" in h.strip().lower()), None)
        for row in reader:
            val = (row.get(email_col) or "").strip().lower() if email_col else ""
            if not val:  # fallback: find an email anywhere in the row
                for cell in row.values():
                    c = (cell or "").strip().lower()
                    if EMAIL_RE.fullmatch(c):
                        val = c
                        break
            if val and EMAIL_RE.fullmatch(val):
                emails.add(val)
    return emails


def fetch_court_reserve(*_args, **_kwargs) -> dict:
    """Return {location_name: set(member_emails)} for every CSV present."""
    result = {}
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*.csv"))):
        loc = canonical_location(path)
        result[loc] = _emails_from_csv(path)
    return result


def last_uploaded_display() -> str:
    """
    Human-readable date the Court Reserve CSVs were last updated. Uses the last
    git commit that touched data/court-reserve/ (robust on CI, where file mtimes
    are reset by checkout); falls back to newest file mtime locally.
    """
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", "--", DATA_DIR],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
        if out:
            dt = datetime.fromisoformat(out)
            return dt.strftime("%B %-d, %Y")
    except Exception:
        pass
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if files:
        dt = datetime.fromtimestamp(max(os.path.getmtime(f) for f in files), tz=timezone.utc)
        return dt.strftime("%B %-d, %Y")
    return "not uploaded yet"
