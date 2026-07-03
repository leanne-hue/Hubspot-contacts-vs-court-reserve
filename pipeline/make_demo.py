"""
Preview the dashboard with synthetic data (no network, no secrets).
    python pipeline/make_demo.py
Writes docs/index.html and outreach_lists/*.xlsx using fake locations/contacts.
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(__file__))

import config
from render import build_dataset, write_excels, render_html

random.seed(7)
DEMO_LOCATIONS = ["Aurora", "Barrie", "Don Mills", "Vaughan", "Windsor"]
FIRST = ["Alex","Sam","Jordan","Priya","Wei","Maria","Liam","Noah","Ava","Omar"]
LAST = ["Smith","Patel","Nguyen","Garcia","Kim","Brown","Singh","Lee","Khan","Rossi"]


def make_contacts():
    contacts, i = [], 0
    for loc in DEMO_LOCATIONS:
        owner = config.derive_owner_email(loc)
        for _ in range(random.randint(150, 400)):
            i += 1
            contacts.append({"first": random.choice(FIRST), "last": random.choice(LAST),
                             "email": f"user{i}@example.com", "owner_email": owner,
                             "owner_name": f"Pickleplex {loc}"})
    return contacts


def make_cr(contacts):
    by_owner = {}
    for c in contacts:
        by_owner.setdefault(c["owner_email"], []).append(c["email"])
    cr = {}
    for loc in DEMO_LOCATIONS:
        emails = by_owner.get(config.derive_owner_email(loc), [])
        keep = set(random.sample(emails, int(len(emails) * random.uniform(.55, .8)))) if emails else set()
        cr[loc] = keep
    return cr


def main():
    contacts = make_contacts()
    data, not_in_cr = build_dataset(contacts, make_cr(contacts), "PREVIEW (synthetic)")
    data["generated_at"] = "PREVIEW (synthetic data) — " + data["generated_at"]
    os.makedirs(config.SITE_DIR, exist_ok=True)
    write_excels(not_in_cr)
    with open(os.path.join(config.SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_html(data))
    open(os.path.join(config.SITE_DIR, ".nojekyll"), "w").close()
    print("Preview written to", config.SITE_DIR)


if __name__ == "__main__":
    main()
