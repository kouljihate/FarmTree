import os
import uuid
import shutil
import logging
from datetime import datetime
from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

logger = logging.getLogger("farmtree")


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trees.json")
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "photos")

_db: TinyDB | None = None
_trees_cache: list[dict] | None = None


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
    result = [_enrich_tree(t) for t in table.all()]
    result.sort(key=lambda x: x.get("last_visit_dt", ""), reverse=True)
    return result


def search_trees(
    query: str = "",
    kind: str | None = None,
    status: str | None = None,
) -> list[dict]:
    db = get_db()
    table = db.table("trees")
    terms = []
    for term in query.strip().split("|"):
        t = term.strip()
        if t:
            terms.append(t.lower())
    result = []
    for tree in table.all():
        if kind and tree.get("kind") != kind:
            continue
        visits = tree.get("visits", [])
        last_status = visits[-1].get("status", "") if visits else ""
        if status and last_status != status:
            continue
        if terms:
            all_found = True
            for term in terms:
                found = (
                    term in (tree.get("kind") or "").lower()
                    or term in (tree.get("variety") or "").lower()
                    or term in (tree.get("tree_code") or "").lower()
                    or any(
                        term in (v.get("notes", "") or "").lower() or term in (v.get("status", "") or "").lower()
                        for v in visits
                    )
                )
                if not found:
                    all_found = False
                    break
            if not all_found:
                continue
        result.append(_enrich_tree(tree))
    result.sort(key=lambda x: x.get("last_visit_dt", ""), reverse=True)
    return result


def invalidate_cache():
    global _trees_cache
    _trees_cache = None


def _enrich_tree(tree) -> dict:
    doc_id = tree.doc_id
    d = dict(tree)
    d["id"] = doc_id
    visits = d.get("visits", [])
    if visits:
        last = visits[-1]
        d.update(
            last_status=last.get("status", ""),
            last_photo=(last.get("photos") or [""])[0],
            last_notes=last.get("notes", ""),
            last_visit_dt=last.get("visit_dt", ""),
        )
    else:
        d.update(last_status="", last_photo="", last_notes="", last_visit_dt="")
    return d


def get_trees_slice(start: int = 0, limit: int = 1000) -> list[dict]:
    global _trees_cache
    db = get_db()
    table = db.table("trees")
    if _trees_cache is None:
        all_docs = table.all()
        _trees_cache = [_enrich_tree(t) for t in all_docs]
        _trees_cache.sort(key=lambda x: x.get("last_visit_dt", ""), reverse=True)
    all_trees = _trees_cache
    total = len(all_trees)
    end = min(start + limit, total)
    return all_trees[start:end]


def count_trees() -> int:
    global _trees_cache
    db = get_db()
    table = db.table("trees")
    if _trees_cache is not None:
        return len(_trees_cache)
    return len(table)


def copy_photo_to_storage(src_path: str) -> str:
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    ext = os.path.splitext(src_path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
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

        except ImportError:
            logger.debug("geocoder not installed, GPS unavailable")
        except Exception as ex:
            logger.warning("GPS geocoding failed: %s", ex)

    threading.Thread(target=get_location, daemon=True).start()