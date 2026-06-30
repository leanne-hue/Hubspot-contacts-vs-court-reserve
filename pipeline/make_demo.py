"""
Generates a realistic PREVIEW of the dashboard using synthetic data, so you can
see the exact layout/UX before the live HubSpot token + Court Reserve run exist.
No network calls. Produces site/index.html and site/downloads/*.xlsx.

    python pipeline/make_demo.py
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(__file__))

import config
from render import build_dataset, write_excels, render_html

random.seed(7)
FIRST = ["Alex","Sam","Jordan","Priya","Wei","Maria","Liam","Noah","Ava","Omar",
         "Sofia","Ethan","Isla","Raj","Chloe","Marcus","Nina","Derek","Tina","Jakob"]
LAST = ["Smith","Patel","Nguyen","Garcia","Kim","Brown","Singh","Lee","Khan","Rossi",
        "Wong","Davis","Murphy","Chen","Lopez","Walters","Ong","Erlich","Culig","Bogacki"]

def email_for(i): return f"user{i}@example.com"

def make_contacts():
    contacts=[]
    i=0
    # give each location-owner a different sized contact base
    for loc in config.COURT_RESERVE_LOCATIONS:
        owner=config.derive_owner_email(loc)
        n=random.randint(180,520)
        for _ in range(n):
            i+=1
            contacts.append({
                "first":random.choice(FIRST),"last":random.choice(LAST),
                "email":email_for(i),"owner_email":owner,
                "owner_name":f"Pickleplex {loc}",
            })
    # a few unassigned
    for _ in range(40):
        i+=1
        contacts.append({"first":random.choice(FIRST),"last":random.choice(LAST),
                         "email":email_for(i),"owner_email":"","owner_name":""})
    return contacts

def make_cr(contacts):
    # For each location, its CR members = a random ~55-80% subset of that owner's
    # contacts (so coverage looks realistic), plus a little cross-location overlap.
    by_owner={}
    for c in contacts: by_owner.setdefault(c["owner_email"],[]).append(c["email"])
    cr={}
    for loc in config.COURT_RESERVE_LOCATIONS:
        owner=config.derive_owner_email(loc)
        emails=by_owner.get(owner,[])
        keep=set(random.sample(emails,int(len(emails)*random.uniform(.55,.8)))) if emails else set()
        # add some members that aren't in HubSpot at all
        for k in range(random.randint(20,60)): keep.add(f"cronly_{loc}_{k}@example.com")
        cr[loc]=keep
    return cr

def main():
    contacts=make_contacts()
    cr=make_cr(contacts)
    data,not_in_cr=build_dataset(contacts,cr)
    data["generated_at"]="PREVIEW (synthetic data) — " + data["generated_at"]
    os.makedirs(config.SITE_DIR,exist_ok=True)
    write_excels(not_in_cr)
    with open(os.path.join(config.SITE_DIR,"index.html"),"w",encoding="utf-8") as f:
        f.write(render_html(data))
    open(os.path.join(config.SITE_DIR,".nojekyll"),"w").close()
    print("Preview written to",config.SITE_DIR)

if __name__=="__main__":
    main()
