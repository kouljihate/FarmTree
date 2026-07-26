import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import init_db, insert_tree
from app.config import TREE_KINDS, TREE_VARIETIES, STATUS_LOOKUP

STATUSES = [s for s in STATUS_LOOKUP.keys() if s != "Dead"]

def random_tree_code(index: int) -> str:
    sector = random.randint(1, 10)
    zone = random.randint(1, 8)
    row = random.randint(1, 20)
    tree_num = random.randint(1, 50)
    return f"S{sector}Z{zone}R{row}T{tree_num}"

def main():
    count = 25000
    init_db()

    kinds = list(TREE_VARIETIES.keys())
    all_varieties = {}
    for k, v in TREE_VARIETIES.items():
        all_varieties[k] = [var for var in v if var != "Other"]

    for i in range(count):
        kind = random.choice(kinds)
        variety = random.choice(all_varieties[kind]) if all_varieties[kind] else "Other"
        status = random.choice(STATUSES)
        lat = round(random.uniform(32.0, 42.0), 6)
        lng = round(random.uniform(-122.0, -114.0), 6)

        insert_tree(
            tree_code=random_tree_code(i),
            kind=kind,
            variety=variety,
            latitude=str(lat),
            longitude=str(lng),
            status=status,
            notes="",
        )

        if (i + 1) % 5000 == 0:
            print(f"Inserted {i + 1}/{count} trees...")

    print(f"Done! {count} trees inserted.")

if __name__ == "__main__":
    main()
