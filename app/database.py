import os
import uuid
import base64
import shutil
import logging
from datetime import datetime
from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

logger = logging.getLogger("farmtree")

try:
    from app.firestore_db import (
        is_available as fs_available,
        insert_tree_firestore,
        get_tree_firestore,
        get_all_trees_firestore,
        update_tree_firestore,
        add_visit_firestore,
        update_tree_status_firestore,
        delete_tree_firestore,
        search_trees_firestore,
        check_tree_code_unique,
    )
except ImportError:
    fs_available = lambda: False

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


def _use_firestore() -> bool:
    try:
        return fs_available()
    except Exception:
        return False


def check_tree_code_unique_local(tree_code: str, exclude_id: int = None) -> bool:
    db = get_db()
    table = db.table("trees")
    for t in table.all():
        if t.get("tree_code") == tree_code:
            if exclude_id is None or t.doc_id != exclude_id:
                return False
    return True


def insert_tree(
    tree_code: str,
    kind: str,
    variety: str,
    latitude: str,
    longitude: str,
    status: str,
    notes: str,
    photos: list[str] | None = None,
    audio: str | None = None,
) -> int | str:
    if _use_firestore():
        result = insert_tree_firestore(tree_code, kind, variety, latitude, longitude, status, notes, photos, audio)
        if result:
            return result
        raise ValueError("Failed to insert tree to Firestore")
    if not check_tree_code_unique_local(tree_code):
        raise ValueError(f"Tree code '{tree_code}' already exists")
    db = get_db()
    table = db.table("trees")
    visit = {
        "visit_dt": datetime.now().strftime("%Y/%m/%d %H:%M"),
        "status": status,
        "notes": notes,
        "photos": photos or [],
        "audio": audio or "",
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


def add_visit(doc_id, status: str, notes: str, photos: list[str] | None = None, audio: str | None = None) -> None:
    if _use_firestore():
        add_visit_firestore(str(doc_id), status, notes, photos, audio)
        return
    db = get_db()
    table = db.table("trees")
    tree = table.get(doc_id=doc_id)
    if tree:
        visit = {
            "visit_dt": datetime.now().strftime("%Y/%m/%d %H:%M"),
            "status": status,
            "notes": notes,
            "photos": photos or [],
            "audio": audio or "",
        }
        visits = tree.get("visits", [])
        visits.append(visit)
        table.update({"visits": visits}, doc_ids=[doc_id])
        invalidate_cache()


def update_tree(
    doc_id,
    tree_code: str | None = None,
    kind: str | None = None,
    variety: str | None = None,
    latitude: str | None = None,
    longitude: str | None = None,
) -> None:
    if _use_firestore():
        update_tree_firestore(str(doc_id), tree_code, kind, variety, latitude, longitude)
        return
    if tree_code and not check_tree_code_unique_local(tree_code, exclude_id=doc_id):
        raise ValueError(f"Tree code '{tree_code}' already exists")
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


def update_tree_status(doc_id, status: str) -> None:
    if _use_firestore():
        update_tree_status_firestore(str(doc_id), status)
        return
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


def delete_tree(doc_id) -> list[str]:
    if _use_firestore():
        delete_tree_firestore(str(doc_id))
        return []
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


def get_tree(doc_id) -> dict | None:
    if _use_firestore():
        return get_tree_firestore(str(doc_id))
    db = get_db()
    table = db.table("trees")
    tree = table.get(doc_id=doc_id)
    if tree:
        tree = dict(tree)
        tree["id"] = doc_id
    return tree


def get_all_trees() -> list[dict]:
    if _use_firestore():
        return get_all_trees_firestore()
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
    if _use_firestore():
        return search_trees_firestore(query, kind, status)
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
    if _trees_cache is None:
        _trees_cache = get_all_trees()
    total = len(_trees_cache)
    end = min(start + limit, total)
    return _trees_cache[start:end]


def count_trees() -> int:
    global _trees_cache
    if _trees_cache is not None:
        return len(_trees_cache)
    return len(get_all_trees())


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


def photo_to_base64(src_path: str, max_size: int = 800) -> str:
    try:
        from PIL import Image as PILImage
        from io import BytesIO
        img = PILImage.open(src_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((max_size, max_size), PILImage.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=75, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except ImportError:
        with open(src_path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception as ex:
        logger.error("Failed to convert photo to base64: %s", ex)
        return ""


def audio_to_base64(src_path: str) -> str:
    try:
        with open(src_path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception as ex:
        logger.error("Failed to convert audio to base64: %s", ex)
        return ""
