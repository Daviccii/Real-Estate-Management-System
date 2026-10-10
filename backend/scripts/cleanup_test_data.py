import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database.database import SessionLocal
from app.models.property import Property

# Matches the fixture-name pattern seen in the dev DB, e.g.
# "Test Property for Status", "Test Property for Payment Auth", etc.
TEST_NAME_PREFIX = "Test Property for"


def main():
    db = SessionLocal()
    try:
        junk = db.query(Property).filter(Property.name.like(f"{TEST_NAME_PREFIX}%")).all()
        print(f"Found {len(junk)} test-fixture properties to remove:")
        for p in junk:
            print(f"  - [{p.id}] {p.name} ({p.city})")
        if not junk:
            print("Nothing to clean up.")
            return
        confirm = input(f"Delete these {len(junk)} rows? [y/N] ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return
        for p in junk:
            db.delete(p)
        db.commit()
        print(f"Deleted {len(junk)} test-fixture properties.")
    finally:
        db.close()


if __name__ == '__main__':
    main()