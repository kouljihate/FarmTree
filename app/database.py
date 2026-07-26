import os
import json
import uuid
import shutil
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

logger = logging.getLogger("farmtree")


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trees.json")
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "photos")

_db: TinyDB | None = None
_raw_docs_cache: list | None = None
_processed_cache: list[dict] | None = None
_processed_count: int = 0


def init_db() -> TinyDB:
    global _db
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    _db = TinyDB(DB_PATH, storage=CachingMiddleware(JSONStorage), indent=4)
    return _db


def get_db() -> TinyDB:
    global _db
    if _db is None:
        _db = init_db()
    return _db


def insert_tree(
    tree_code: str,
    kind: str,
    variety: str,
    latitude: str,
    longitude: str,
    status: str,
    notes: str,
    photos: list[str] | None = None,
) -> int:
    db = get_db()
    table = db.table("trees")
    visit = {
        "visit_dt": datetime.now().strftime("%Y/%m/%d %H:%M"),
        "status": status,
        "notes": notes,
        "photos": photos or [],
    }
    doc = {
        "tree_code": tree_code,
        "kind": kind,
        "variety": variety,
        "latitude": latitude,
        "longitude": longitude,
        "visits": [visit],
    }
    doc_id = table.insert(doc)
    invalidate_cache()
    return doc_id


def add_visit(doc_id: int, status: str, notes: str, photos: list[str] | None = None) -> None:
    db = get_db()
    table = db.table("trees")
    tree = table.get(doc_id=doc_id)
    if tree:
        visit = {
            "visit_dt": datetime.now().strftime("%Y/%m/%d %H:%M"),
            "status": status,
            "notes": notes,
            "photos": photos or [],
        }
        visits = tree.get("visits", [])
        visits.append(visit)
        table.update({"visits": visits}, doc_ids=[doc_id])
        invalidate_cache()


def update_tree(
    doc_id: int,
    tree_code: str | None = None,
    kind: str | None = None,
    variety: str | None = None,
    latitude: str | None = None,
    longitude: str | None = None,
) -> None:
    db = get_db()
    table = db.table("trees")
    updates = {}
    if tree_code is not None:
        updates["tree_code"] = tree_code
    if kind is not None:
        updates["kind"] = kind
    if variety is not None:
        updates["variety"] = variety
    if latitude is not None:
        updates["latitude"] = latitude
    if longitude is not None:
        updates["longitude"] = longitude
    if updates:
        table.update(updates, doc_ids=[doc_id])
        invalidate_cache()


def update_tree_status(doc_id: int, status: str) -> None:
    db = get_db()
    table = db.table("trees")
    tree = table.get(doc_id=doc_id)
    if tree:
        visit = {
            "visit_dt": datetime.now().strftime("%Y/%m/%d %H:%M"),
            "status": status,
            "notes": "",
            "photos": [],
        }
        visits = tree.get("visits", [])
        visits.append(visit)
        table.update({"visits": visits}, doc_ids=[doc_id])
        invalidate_cache()


def delete_tree(doc_id: int) -> list[str]:
    db = get_db()
    table = db.table("trees")
    tree = table.get(doc_id=doc_id)
    photo_paths = []
    if tree:
        for visit in tree.get("visits", []):
            for photo in visit.get("photos", []):
                photo_paths.append(photo)
    table.remove(doc_ids=[doc_id])
    invalidate_cache()
    return photo_paths


def get_tree(doc_id: int) -> dict | None:
    db = get_db()
    table = db.table("trees")
    tree = table.get(doc_id=doc_id)
    if tree:
        tree = dict(tree)
        tree["id"] = doc_id
    return tree


def get_all_trees() -> list[dict]:
    db = get_db()
    table = db.table("trees")
    trees = table.all()
    result = []
    for tree in trees:
        doc_id = tree.doc_id
        tree_dict = dict(tree)
        tree_dict["id"] = doc_id
        visits = tree_dict.get("visits", [])
        if visits:
            last_visit = visits[-1]
            tree_dict["last_status"] = last_visit.get("status", "")
            tree_dict["last_photo"] = last_visit.get("photos", [""])[0] if last_visit.get("photos") else ""
            tree_dict["last_notes"] = last_visit.get("notes", "")
            tree_dict["last_visit_dt"] = last_visit.get("visit_dt", "")
        else:
            tree_dict["last_status"] = ""
            tree_dict["last_photo"] = ""
            tree_dict["last_notes"] = ""
            tree_dict["last_visit_dt"] = ""
        result.append(tree_dict)
    result.sort(key=lambda x: x.get("last_visit_dt", ""), reverse=True)
    return result


def get_trees_page(page: int, per_page: int) -> list[dict]:
    all_trees = get_all_trees()
    start = page * per_page
    end = start + per_page
    return all_trees[start:end]


def search_trees(
    query: str = "",
    kind: str | None = None,
    status: str | None = None,
) -> list[dict]:
    db = get_db()
    table = db.table("trees")
    q = query.lower().strip()
    raw_trees = table.all()
    result = []
    for tree in raw_trees:
        tree_dict = dict(tree)
        if kind and tree_dict.get("kind") != kind:
            continue
        last_status = ""
        visits = tree_dict.get("visits", [])
        if visits:
            last_visit = visits[-1]
            last_status = last_visit.get("status", "")
            if status and last_status != status:
                continue
        elif status:
            continue
        if q:
            if q in (tree_dict.get("kind") or "").lower():
                pass
            elif q in (tree_dict.get("variety") or "").lower():
                pass
            elif q in (tree_dict.get("tree_code") or "").lower():
                pass
            else:
                found_in_visit = False
                for v in visits:
                    if q in (v.get("notes", "") or "").lower() or q in (v.get("status", "") or "").lower():
                        found_in_visit = True
                        break
                if not found_in_visit:
                    continue
        doc_id = tree.doc_id
        tree_dict["id"] = doc_id
        if visits:
            last_visit = visits[-1]
            tree_dict["last_status"] = last_visit.get("status", "")
            tree_dict["last_photo"] = last_visit.get("photos", [""])[0] if last_visit.get("photos") else ""
            tree_dict["last_notes"] = last_visit.get("notes", "")
            tree_dict["last_visit_dt"] = last_visit.get("visit_dt", "")
        else:
            tree_dict["last_status"] = ""
            tree_dict["last_photo"] = ""
            tree_dict["last_notes"] = ""
            tree_dict["last_visit_dt"] = ""
        result.append(tree_dict)
    result.sort(key=lambda x: x.get("last_visit_dt", ""), reverse=True)
    return result


def invalidate_cache():
    global _raw_docs_cache, _processed_cache, _processed_count
    _raw_docs_cache = None
    _processed_cache = None
    _processed_count = 0


def get_trees_slice(start: int = 0, limit: int = 1000) -> list[dict]:
    global _raw_docs_cache, _processed_cache, _processed_count
    db = get_db()
    table = db.table("trees")
    if _raw_docs_cache is None:
        _raw_docs_cache = table.all()
        _processed_cache = []
        _processed_count = 0
    all_docs = _raw_docs_cache
    total = len(all_docs)
    end = min(start + limit, total)

    if end <= _processed_count:
        return _processed_cache[start:end]

    for tree in all_docs[_processed_count:end]:
        doc_id = tree.doc_id
        tree_dict = dict(tree)
        tree_dict["id"] = doc_id
        visits = tree_dict.get("visits", [])
        if visits:
            last_visit = visits[-1]
            tree_dict["last_status"] = last_visit.get("status", "")
            tree_dict["last_photo"] = last_visit.get("photos", [""])[0] if last_visit.get("photos") else ""
            tree_dict["last_notes"] = last_visit.get("notes", "")
            tree_dict["last_visit_dt"] = last_visit.get("visit_dt", "")
        else:
            tree_dict["last_status"] = ""
            tree_dict["last_photo"] = ""
            tree_dict["last_notes"] = ""
            tree_dict["last_visit_dt"] = ""
        _processed_cache.append(tree_dict)
    _processed_count = end

    _processed_cache.sort(key=lambda x: x.get("last_visit_dt", ""), reverse=True)
    return _processed_cache[start:end]


def count_trees() -> int:
    db = get_db()
    table = db.table("trees")
    return len(table)


def copy_photo_to_storage(src_path: str) -> str:
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    ext = os.path.splitext(src_path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%y%m%d%H%M')}{ext}"
    dst_path = os.path.join(PHOTOS_DIR, filename)
    try:
        shutil.copy2(src_path, dst_path)
    except Exception as ex:
        logger.error("Failed to copy photo %s -> %s: %s", src_path, dst_path, ex)
    return dst_path


def get_gps_coordinates(callback):
    import threading

    def get_location():
        try:
            import geocoder
            g = geocoder.ip("me")
            if g.latlng:
                callback(str(g.latlng[0]), str(g.latlng[1]))
        except Exception as ex:
            logger.warning("GPS geocoding failed: %s", ex)

    threading.Thread(target=get_location, daemon=True).start()