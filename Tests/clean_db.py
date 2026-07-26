#!/usr/bin/env python3
"""Delete all Farm Tree Manager data: tree records and captured photos.

Uses the same database module the app uses, so it wipes exactly what the
app reads/writes:
  - data/trees.json  (all tree + visit records)
  - data/photos/     (all captured photo files)

Run from the project root:
    python tests/clean_db.py
"""

import os
import shutil
import sys

# Make project root importable so `app.database` resolves.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import database  # noqa: E402


def main() -> None:
    db = database.get_db()
    tree_table = db.table("trees")

    tree_count = len(tree_table)
    photos_dir = database.PHOTOS_DIR

    # 1. Count and remove photo files referenced by trees.
    removed_photos = 0
    for doc in tree_table.all():
        for visit in doc.get("visits", []):
            for photo in visit.get("photos", []):
                if photo and os.path.exists(photo):
                    try:
                        os.remove(photo)
                        removed_photos += 1
                    except OSError as exc:
                        print(f"  ! Could not remove {photo}: {exc}")

    # 2. Remove any orphaned files left in the photos directory.
    orphan_photos = 0
    if os.path.isdir(photos_dir):
        for name in os.listdir(photos_dir):
            path = os.path.join(photos_dir, name)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    orphan_photos += 1
                except OSError as exc:
                    print(f"  ! Could not remove {path}: {exc}")

    # 3. Clear all tree records (truncate the table).
    tree_table.truncate()
    db.storage.flush()
    db.close()

    print(f"Deleted {tree_count} tree record(s).")
    print(f"Removed {removed_photos} photo file(s) referenced by trees.")
    print(f"Removed {orphan_photos} orphaned file(s) in {photos_dir}.")
    print(f"Database file: {database.DB_PATH}")
    if os.path.exists(database.DB_PATH):
        print(f"  -> {database.DB_PATH} still exists but is now empty.")


if __name__ == "__main__":
    main()
